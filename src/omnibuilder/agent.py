"""
OmniBuilder Agent Orchestrator

The main agent that coordinates all components to autonomously
execute development tasks.
"""

import asyncio
from typing import Any, Dict, List, Optional

from omnibuilder.config import Config
from omnibuilder.models import (
    AgentState,
    Context,
    ExecutionPlan,
    Message,
    TaskStatus,
)

# Core components
from omnibuilder.core.planner import Planner, GoalDecomposer
from omnibuilder.core.selector import ToolSelector
from omnibuilder.core.reasoning import ReasoningEngine
from omnibuilder.core.memory_ltm import LongTermMemoryManager
from omnibuilder.core.memory_stm import WorkingMemoryManager
from omnibuilder.core.error_handler import ErrorHandler, SelfCorrector
from omnibuilder.core.generator import CodeGenerator, ArtifactGenerator
from omnibuilder.core.formatter import OutputFormatter

# Environment components
from omnibuilder.environment.codebase import CodebaseContextProvider
from omnibuilder.environment.terminal import TerminalExecutionAgent
from omnibuilder.environment.filesystem import FileSystemManager
from omnibuilder.environment.local_llm import LocalInferenceHandler
from omnibuilder.environment.safety import SafetyPrompt


class LLMClient:
    """Simple LLM client wrapper."""

    def __init__(self, config: Config):
        self.config = config
        self._client = None

    async def initialize(self) -> None:
        """Initialize the LLM client based on config."""
        provider = self.config.llm.provider

        if provider == "anthropic":
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.config.llm.api_key)
            except ImportError:
                pass
        elif provider == "openai":
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.config.llm.api_key)
            except ImportError:
                pass

    async def complete(self, prompt: str, system: str = "") -> str:
        """Get completion from LLM."""
        if not self._client:
            return "LLM client not initialized"

        provider = self.config.llm.provider

        try:
            if provider == "anthropic":
                response = await self._client.messages.create(
                    model=self.config.llm.model,
                    max_tokens=self.config.llm.max_tokens,
                    system=system or "You are OmniBuilder, an autonomous development agent.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

            elif provider == "openai":
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                response = await self._client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=messages,
                    max_tokens=self.config.llm.max_tokens,
                    temperature=self.config.llm.temperature
                )
                return response.choices[0].message.content

        except Exception as e:
            return f"Error: {str(e)}"

        return "Unsupported provider"


class OmniBuilderAgent:
    """
    The main OmniBuilder autonomous agent.

    Coordinates all components to plan, execute, and manage
    development tasks end-to-end.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
        self.state = AgentState()

        # Initialize LLM client
        self.llm = LLMClient(self.config)

        # Initialize core components
        self.planner = Planner(GoalDecomposer(self.llm))
        self.tool_selector = ToolSelector(self.llm)
        self.reasoning = ReasoningEngine(self.llm)
        self.ltm = LongTermMemoryManager(self.config.memory.memory_db_path)
        self.stm = WorkingMemoryManager()
        self.error_handler = ErrorHandler(self.llm)
        self.self_corrector = SelfCorrector(self.error_handler)
        self.code_generator = CodeGenerator(self.llm)
        self.artifact_generator = ArtifactGenerator()
        self.formatter = OutputFormatter()

        # Initialize environment components
        self.codebase = CodebaseContextProvider(self.config.working_directory)
        self.terminal = TerminalExecutionAgent(
            safe_mode=self.config.safety.safe_mode,
            working_dir=self.config.working_directory
        )
        self.filesystem = FileSystemManager()
        self.local_llm = LocalInferenceHandler()
        self.safety = SafetyPrompt()

    async def initialize(self) -> None:
        """Initialize all async components."""
        await self.llm.initialize()

        # Index codebase
        self.codebase.index_codebase()

    async def run(self, goal: str) -> str:
        """
        Execute a goal autonomously.

        Args:
            goal: The high-level goal to achieve

        Returns:
            Summary of execution
        """
        self.state.is_running = True
        self.state.current_task = goal

        # Add to conversation history
        self.state.conversation_history.append(
            Message(role="user", content=goal)
        )

        try:
            # 1. Plan the task
            plan = await self.planner.create_execution_plan(goal)
            self.state.execution_plan = plan

            # 2. Create execution context
            context = Context(
                task_id=plan.id,
                working_directory=self.config.working_directory,
                environment=self.terminal.get_environment()
            )
            self.state.context = context

            # 3. Execute plan steps
            results = []
            for step in plan.steps:
                self.state.current_step = step.id
                step.status = TaskStatus.IN_PROGRESS

                try:
                    result = await self._execute_step(step, context)
                    step.status = TaskStatus.COMPLETED
                    step.result = result
                    results.append({"step": step.description, "success": True, "result": result})

                    # Update context
                    self.stm.add_output(str(result), step.tool_name or "unknown")

                except Exception as e:
                    # Handle error with self-correction
                    analysis = self.error_handler.analyze_error(e)
                    fix = await self.error_handler.generate_fix(e)

                    step.status = TaskStatus.FAILED
                    step.error = str(e)
                    results.append({
                        "step": step.description,
                        "success": False,
                        "error": str(e),
                        "fix_suggestion": fix.steps
                    })

                    self.stm.add_error(str(e), step.tool_name or "unknown")

            # 4. Generate summary
            summary = self.formatter.generate_summary(results, f"Execution: {goal}")

            # Store in long-term memory
            self.ltm.store_solution(goal, str(summary.overview), {
                "plan_id": plan.id,
                "status": summary.status
            })

            # Add to conversation
            self.state.conversation_history.append(
                Message(role="assistant", content=summary.overview)
            )

            return summary.overview

        finally:
            self.state.is_running = False
            self.state.current_task = None
            self.state.current_step = None

    async def _execute_step(self, step: Any, context: Context) -> Any:
        """Execute a single step of the plan."""
        # Select appropriate tool
        tool = await self.tool_selector.select_tool(
            context,
            step.description
        )

        if not tool:
            # Use reasoning to handle step
            result = await self.reasoning.reason(context, step.description)
            return result.conclusion

        # Check if confirmation required
        if tool.requires_confirmation:
            from omnibuilder.environment.safety import Action
            action = Action(
                name=tool.name,
                description=step.description,
                command=step.parameters.get("command")
            )

            approved = await self.safety.confirm_action(action)
            if not approved:
                return "Action cancelled by user"

        # Execute based on tool type
        if tool.name == "execute_shell":
            result = await self.terminal.execute_shell(
                step.parameters.get("command", ""),
                timeout=step.parameters.get("timeout", 30)
            )
            return result.output if result.success else result.error

        elif tool.name == "read_file":
            return self.filesystem.read_file(step.parameters.get("path", ""))

        elif tool.name == "write_file":
            success = self.filesystem.write_file(
                step.parameters.get("path", ""),
                step.parameters.get("content", "")
            )
            return "File written" if success else "Failed to write file"

        elif tool.name == "search_code":
            matches = self.codebase.search_code(
                step.parameters.get("query", ""),
                step.parameters.get("file_pattern", "*")
            )
            return f"Found {len(matches)} matches"

        elif tool.name == "generate_code":
            from omnibuilder.core.generator import CodeSpec
            spec = CodeSpec(
                description=step.parameters.get("spec", step.description),
                language=step.parameters.get("language", "python")
            )
            return await self.code_generator.generate_code(spec)

        else:
            # Fallback to reasoning
            result = await self.reasoning.reason(context, step.description)
            return result.conclusion

    async def chat(self, message: str) -> str:
        """
        Interactive chat with the agent.

        Args:
            message: User message

        Returns:
            Agent response
        """
        # Add to history
        self.state.conversation_history.append(
            Message(role="user", content=message)
        )

        # Determine if this is a task or question
        task_indicators = ["create", "build", "implement", "fix", "update", "add", "remove", "deploy"]

        is_task = any(indicator in message.lower() for indicator in task_indicators)

        if is_task:
            response = await self.run(message)
        else:
            # Answer question using reasoning
            result = await self.reasoning.reason(
                self.state.context or Context(
                    task_id="chat",
                    working_directory=self.config.working_directory
                ),
                message
            )
            response = result.conclusion

        # Add response to history
        self.state.conversation_history.append(
            Message(role="assistant", content=response)
        )

        return response

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state."""
        return {
            "is_running": self.state.is_running,
            "current_task": self.state.current_task,
            "current_step": self.state.current_step,
            "plan_status": self.state.execution_plan.status.value if self.state.execution_plan else None,
            "message_count": len(self.state.conversation_history)
        }

    async def stop(self) -> None:
        """Stop the agent gracefully."""
        self.state.is_running = False

        # Close async resources
        await self.local_llm.close()
