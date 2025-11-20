"""
P1.1 Goal Decomposer & Planner

Breaks high-level tasks into discrete, ordered steps and creates execution plans.
"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from omnibuilder.models import (
    TaskStep,
    ExecutionPlan,
    ComplexityScore,
    TaskStatus,
    RiskLevel,
)


class GoalDecomposer:
    """Decomposes high-level goals into actionable steps."""

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client

    async def decompose_task(self, goal: str, context: Optional[Dict] = None) -> List[TaskStep]:
        """
        Break down a high-level goal into discrete, ordered steps.

        Args:
            goal: The high-level goal to decompose
            context: Optional context about the project/environment

        Returns:
            List of TaskStep objects representing the decomposed task
        """
        # This will use LLM to decompose the task
        prompt = self._build_decomposition_prompt(goal, context)

        if self.llm_client:
            response = await self.llm_client.complete(prompt)
            steps = self._parse_steps_response(response)
        else:
            # Default decomposition for simple tasks
            steps = [
                TaskStep(
                    id=str(uuid.uuid4()),
                    description=goal,
                    status=TaskStatus.PENDING
                )
            ]

        return steps

    def _build_decomposition_prompt(self, goal: str, context: Optional[Dict]) -> str:
        """Build the prompt for task decomposition."""
        context_str = ""
        if context:
            context_str = f"\n\nContext:\n{context}"

        return f"""Decompose the following goal into discrete, actionable steps.
Each step should be specific and executable.

Goal: {goal}{context_str}

Return a JSON array of steps with:
- description: what needs to be done
- dependencies: list of step indices this depends on
- tool_name: suggested tool to use (if applicable)
- estimated_minutes: estimated time to complete

Format as JSON array."""

    def _parse_steps_response(self, response: str) -> List[TaskStep]:
        """Parse LLM response into TaskStep objects."""
        import json

        try:
            steps_data = json.loads(response)
            steps = []

            for i, step_data in enumerate(steps_data):
                step = TaskStep(
                    id=str(uuid.uuid4()),
                    description=step_data.get("description", ""),
                    dependencies=[str(d) for d in step_data.get("dependencies", [])],
                    tool_name=step_data.get("tool_name"),
                    status=TaskStatus.PENDING
                )
                steps.append(step)

            return steps
        except json.JSONDecodeError:
            # Fallback: create single step
            return [
                TaskStep(
                    id=str(uuid.uuid4()),
                    description=response,
                    status=TaskStatus.PENDING
                )
            ]

    async def estimate_complexity(self, task: str) -> ComplexityScore:
        """
        Estimate the complexity of a task.

        Args:
            task: Task description

        Returns:
            ComplexityScore with various complexity metrics
        """
        # Simple heuristic-based estimation
        # In production, this would use LLM for better estimation

        word_count = len(task.split())

        # Base complexity on task length and keywords
        cognitive = min(10.0, word_count / 10)
        technical = 5.0  # Default medium

        # Adjust based on keywords
        complex_keywords = ["integrate", "optimize", "refactor", "architect", "design"]
        simple_keywords = ["add", "update", "fix", "change"]

        task_lower = task.lower()
        if any(kw in task_lower for kw in complex_keywords):
            technical += 2.0
            cognitive += 1.0
        if any(kw in task_lower for kw in simple_keywords):
            technical -= 1.0

        technical = max(0.0, min(10.0, technical))
        overall = (cognitive + technical) / 2

        time_estimate = int(overall * 10)  # minutes

        risk_level = RiskLevel.LOW
        if overall > 7:
            risk_level = RiskLevel.HIGH
        elif overall > 4:
            risk_level = RiskLevel.MEDIUM

        return ComplexityScore(
            overall=overall,
            cognitive=cognitive,
            technical=technical,
            time_estimate=time_estimate,
            risk_level=risk_level
        )


class Planner:
    """Creates and manages execution plans."""

    def __init__(self, decomposer: Optional[GoalDecomposer] = None):
        self.decomposer = decomposer or GoalDecomposer()

    async def create_execution_plan(
        self,
        goal: str,
        context: Optional[Dict] = None
    ) -> ExecutionPlan:
        """
        Create a complete execution plan for a goal.

        Args:
            goal: The goal to plan for
            context: Optional context information

        Returns:
            ExecutionPlan with ordered steps
        """
        steps = await self.decomposer.decompose_task(goal, context)
        complexity = await self.decomposer.estimate_complexity(goal)

        plan = ExecutionPlan(
            id=str(uuid.uuid4()),
            goal=goal,
            steps=steps,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            estimated_duration=complexity.time_estimate * 60  # convert to seconds
        )

        return plan

    def prioritize_steps(self, steps: List[TaskStep]) -> List[TaskStep]:
        """
        Order steps by priority and dependencies.

        Args:
            steps: List of steps to prioritize

        Returns:
            Ordered list of steps
        """
        # Topological sort based on dependencies
        ordered = []
        remaining = steps.copy()
        completed_ids = set()

        while remaining:
            # Find steps with all dependencies satisfied
            ready = [
                s for s in remaining
                if all(dep in completed_ids for dep in s.dependencies)
            ]

            if not ready:
                # Circular dependency or invalid - add remaining as-is
                ordered.extend(remaining)
                break

            # Sort ready steps by some priority (could be enhanced)
            ready.sort(key=lambda s: len(s.dependencies))

            for step in ready:
                ordered.append(step)
                completed_ids.add(step.id)
                remaining.remove(step)

        return ordered

    def update_plan_status(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Update the overall plan status based on step statuses."""
        statuses = [step.status for step in plan.steps]

        if all(s == TaskStatus.COMPLETED for s in statuses):
            plan.status = TaskStatus.COMPLETED
        elif any(s == TaskStatus.FAILED for s in statuses):
            plan.status = TaskStatus.FAILED
        elif any(s == TaskStatus.IN_PROGRESS for s in statuses):
            plan.status = TaskStatus.IN_PROGRESS
        elif any(s == TaskStatus.BLOCKED for s in statuses):
            plan.status = TaskStatus.BLOCKED

        return plan
