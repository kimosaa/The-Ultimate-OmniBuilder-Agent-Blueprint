"""
Tests for the core planner module.
"""

import pytest
from omnibuilder.core.planner import GoalDecomposer, Planner
from omnibuilder.models import TaskStatus


class TestGoalDecomposer:
    """Tests for GoalDecomposer."""

    @pytest.fixture
    def decomposer(self):
        return GoalDecomposer()

    @pytest.mark.asyncio
    async def test_decompose_simple_task(self, decomposer):
        """Test decomposing a simple task."""
        steps = await decomposer.decompose_task("Create a hello world script")

        assert len(steps) >= 1
        assert all(step.status == TaskStatus.PENDING for step in steps)
        assert all(step.id for step in steps)

    @pytest.mark.asyncio
    async def test_estimate_complexity(self, decomposer):
        """Test complexity estimation."""
        complexity = await decomposer.estimate_complexity("Add user authentication")

        assert 0 <= complexity.overall <= 10
        assert 0 <= complexity.cognitive <= 10
        assert 0 <= complexity.technical <= 10
        assert complexity.time_estimate > 0
        assert complexity.risk_level is not None

    @pytest.mark.asyncio
    async def test_estimate_complexity_simple(self, decomposer):
        """Test complexity for simple task."""
        complexity = await decomposer.estimate_complexity("Fix typo")

        assert complexity.overall < 5  # Should be low complexity

    @pytest.mark.asyncio
    async def test_estimate_complexity_complex(self, decomposer):
        """Test complexity for complex task."""
        complexity = await decomposer.estimate_complexity(
            "Design and architect a distributed microservices system"
        )

        assert complexity.overall > 5  # Should be higher complexity


class TestPlanner:
    """Tests for Planner."""

    @pytest.fixture
    def planner(self):
        return Planner()

    @pytest.mark.asyncio
    async def test_create_execution_plan(self, planner):
        """Test creating an execution plan."""
        plan = await planner.create_execution_plan("Build a REST API")

        assert plan.id
        assert plan.goal == "Build a REST API"
        assert len(plan.steps) >= 1
        assert plan.status == TaskStatus.PENDING
        assert plan.estimated_duration > 0

    def test_prioritize_steps_no_dependencies(self, planner):
        """Test prioritizing steps without dependencies."""
        from omnibuilder.models import TaskStep
        import uuid

        steps = [
            TaskStep(id=str(uuid.uuid4()), description="Step 1"),
            TaskStep(id=str(uuid.uuid4()), description="Step 2"),
            TaskStep(id=str(uuid.uuid4()), description="Step 3"),
        ]

        ordered = planner.prioritize_steps(steps)

        assert len(ordered) == 3

    def test_prioritize_steps_with_dependencies(self, planner):
        """Test prioritizing steps with dependencies."""
        from omnibuilder.models import TaskStep
        import uuid

        step1_id = str(uuid.uuid4())
        step2_id = str(uuid.uuid4())
        step3_id = str(uuid.uuid4())

        steps = [
            TaskStep(id=step3_id, description="Step 3", dependencies=[step1_id, step2_id]),
            TaskStep(id=step1_id, description="Step 1"),
            TaskStep(id=step2_id, description="Step 2", dependencies=[step1_id]),
        ]

        ordered = planner.prioritize_steps(steps)

        # Step 1 should come first, then Step 2, then Step 3
        assert ordered[0].id == step1_id
        assert ordered[1].id == step2_id
        assert ordered[2].id == step3_id

    def test_update_plan_status(self, planner):
        """Test updating plan status based on steps."""
        from omnibuilder.models import ExecutionPlan, TaskStep
        import uuid

        steps = [
            TaskStep(id=str(uuid.uuid4()), description="Step 1", status=TaskStatus.COMPLETED),
            TaskStep(id=str(uuid.uuid4()), description="Step 2", status=TaskStatus.COMPLETED),
        ]

        plan = ExecutionPlan(
            id=str(uuid.uuid4()),
            goal="Test",
            steps=steps
        )

        updated = planner.update_plan_status(plan)
        assert updated.status == TaskStatus.COMPLETED

    def test_update_plan_status_with_failure(self, planner):
        """Test plan status when a step fails."""
        from omnibuilder.models import ExecutionPlan, TaskStep
        import uuid

        steps = [
            TaskStep(id=str(uuid.uuid4()), description="Step 1", status=TaskStatus.COMPLETED),
            TaskStep(id=str(uuid.uuid4()), description="Step 2", status=TaskStatus.FAILED),
        ]

        plan = ExecutionPlan(
            id=str(uuid.uuid4()),
            goal="Test",
            steps=steps
        )

        updated = planner.update_plan_status(plan)
        assert updated.status == TaskStatus.FAILED
