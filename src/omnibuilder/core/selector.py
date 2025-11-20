"""
P1.2 Tool/Function Selector

Determines which external function or internal tool to call next.
"""

from typing import Any, Dict, List, Optional
from omnibuilder.models import Tool, Context, ToolCategory, RiskLevel


class ValidationResult:
    """Result of parameter validation."""

    def __init__(self, valid: bool, errors: List[str] = None):
        self.valid = valid
        self.errors = errors or []


class CostEstimate:
    """Estimated cost of tool execution."""

    def __init__(self, time_seconds: float, risk: RiskLevel, tokens: int = 0):
        self.time_seconds = time_seconds
        self.risk = risk
        self.tokens = tokens


class ToolSelector:
    """Selects and validates tools for task execution."""

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client
        self._tools: Dict[str, Tool] = {}
        self._initialize_default_tools()

    def _initialize_default_tools(self) -> None:
        """Initialize the default set of available tools."""
        default_tools = [
            # Core tools
            Tool(
                name="execute_shell",
                description="Execute a shell command",
                category=ToolCategory.ENVIRONMENT,
                parameters={"command": "str", "timeout": "int", "cwd": "str"},
                required_params=["command"],
                risk_level=RiskLevel.MEDIUM,
                requires_confirmation=False
            ),
            Tool(
                name="read_file",
                description="Read contents of a file",
                category=ToolCategory.ENVIRONMENT,
                parameters={"path": "str", "encoding": "str"},
                required_params=["path"],
                risk_level=RiskLevel.LOW
            ),
            Tool(
                name="write_file",
                description="Write contents to a file",
                category=ToolCategory.ENVIRONMENT,
                parameters={"path": "str", "content": "str", "encoding": "str"},
                required_params=["path", "content"],
                risk_level=RiskLevel.MEDIUM
            ),
            Tool(
                name="search_code",
                description="Search for code patterns in codebase",
                category=ToolCategory.ENVIRONMENT,
                parameters={"query": "str", "file_pattern": "str", "path": "str"},
                required_params=["query"],
                risk_level=RiskLevel.LOW
            ),
            Tool(
                name="git_commit",
                description="Commit changes to git",
                category=ToolCategory.VERSION_CONTROL,
                parameters={"message": "str", "files": "list"},
                required_params=["message"],
                risk_level=RiskLevel.MEDIUM
            ),
            Tool(
                name="git_push",
                description="Push commits to remote",
                category=ToolCategory.VERSION_CONTROL,
                parameters={"remote": "str", "branch": "str"},
                required_params=[],
                risk_level=RiskLevel.HIGH,
                requires_confirmation=True
            ),
            Tool(
                name="search_web",
                description="Search the web for information",
                category=ToolCategory.WEB_RESEARCH,
                parameters={"query": "str", "num_results": "int"},
                required_params=["query"],
                risk_level=RiskLevel.LOW
            ),
            Tool(
                name="generate_code",
                description="Generate code from specification",
                category=ToolCategory.CORE,
                parameters={"spec": "str", "language": "str"},
                required_params=["spec"],
                risk_level=RiskLevel.LOW
            ),
        ]

        for tool in default_tools:
            self._tools[tool.name] = tool

    def register_tool(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self, category: Optional[ToolCategory] = None) -> List[Tool]:
        """List all available tools, optionally filtered by category."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    async def select_tool(
        self,
        context: Context,
        task_description: str,
        available_tools: Optional[List[Tool]] = None
    ) -> Optional[Tool]:
        """
        Select the optimal tool for the current task.

        Args:
            context: Current execution context
            task_description: Description of what needs to be done
            available_tools: Optional list of tools to choose from

        Returns:
            Selected Tool or None if no suitable tool found
        """
        tools = available_tools or list(self._tools.values())

        if not tools:
            return None

        # Simple keyword-based selection
        # In production, use LLM for better selection
        task_lower = task_description.lower()

        # Scoring based on keyword matching
        scores: Dict[str, float] = {}

        for tool in tools:
            score = 0.0
            tool_words = tool.name.lower().replace("_", " ").split()
            desc_words = tool.description.lower().split()

            for word in tool_words + desc_words:
                if word in task_lower:
                    score += 1.0

            # Boost for exact matches
            if tool.name.lower() in task_lower:
                score += 5.0

            scores[tool.name] = score

        # Select highest scoring tool
        if scores:
            best_tool_name = max(scores, key=scores.get)
            if scores[best_tool_name] > 0:
                return self._tools[best_tool_name]

        return None

    def validate_tool_params(self, tool: Tool, params: Dict[str, Any]) -> ValidationResult:
        """
        Validate parameters for a tool.

        Args:
            tool: The tool to validate for
            params: Parameters to validate

        Returns:
            ValidationResult indicating if params are valid
        """
        errors = []

        # Check required parameters
        for req_param in tool.required_params:
            if req_param not in params:
                errors.append(f"Missing required parameter: {req_param}")
            elif params[req_param] is None:
                errors.append(f"Required parameter '{req_param}' is None")

        # Type checking (basic)
        for param_name, param_value in params.items():
            if param_name in tool.parameters:
                expected_type = tool.parameters[param_name]
                if expected_type == "str" and not isinstance(param_value, str):
                    errors.append(f"Parameter '{param_name}' should be string")
                elif expected_type == "int" and not isinstance(param_value, int):
                    errors.append(f"Parameter '{param_name}' should be integer")
                elif expected_type == "list" and not isinstance(param_value, list):
                    errors.append(f"Parameter '{param_name}' should be list")

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def get_tool_alternatives(self, tool: Tool) -> List[Tool]:
        """
        Find alternative tools that can perform similar functions.

        Args:
            tool: The primary tool

        Returns:
            List of alternative tools
        """
        alternatives = []

        for t in self._tools.values():
            if t.name != tool.name and t.category == tool.category:
                alternatives.append(t)

        return alternatives

    def estimate_tool_cost(self, tool: Tool, params: Dict[str, Any]) -> CostEstimate:
        """
        Estimate the cost (time, risk, resources) of using a tool.

        Args:
            tool: The tool to estimate for
            params: Parameters that will be used

        Returns:
            CostEstimate with time and risk information
        """
        # Base estimates
        base_times = {
            ToolCategory.CORE: 1.0,
            ToolCategory.ENVIRONMENT: 2.0,
            ToolCategory.VERSION_CONTROL: 3.0,
            ToolCategory.WEB_RESEARCH: 5.0,
            ToolCategory.CLOUD: 30.0,
            ToolCategory.DATA: 10.0,
            ToolCategory.COMMUNICATION: 5.0,
            ToolCategory.VISUALIZATION: 3.0,
            ToolCategory.DEBUGGING: 5.0,
        }

        time_estimate = base_times.get(tool.category, 5.0)

        # Adjust based on parameters
        if "timeout" in params:
            time_estimate = max(time_estimate, params["timeout"])

        return CostEstimate(
            time_seconds=time_estimate,
            risk=tool.risk_level,
            tokens=0
        )
