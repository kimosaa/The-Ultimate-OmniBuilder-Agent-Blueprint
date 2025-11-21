"""
Tests for data models.
"""

import pytest
from datetime import datetime

from omnibuilder.models import (
    TaskStep,
    ExecutionPlan,
    TaskStatus,
    RiskLevel,
    Tool,
    ToolCategory,
    Context,
    Message,
    ExecutionResult,
)


class TestTaskStep:
    """Tests for TaskStep model."""

    def test_create_task_step(self):
        """Test creating a task step."""
        step = TaskStep(
            id="test-1",
            description="Test step"
        )

        assert step.id == "test-1"
        assert step.description == "Test step"
        assert step.status == TaskStatus.PENDING
        assert step.dependencies == []
        assert step.result is None

    def test_task_step_with_dependencies(self):
        """Test task step with dependencies."""
        step = TaskStep(
            id="test-1",
            description="Test step",
            dependencies=["dep-1", "dep-2"]
        )

        assert len(step.dependencies) == 2
        assert "dep-1" in step.dependencies


class TestExecutionPlan:
    """Tests for ExecutionPlan model."""

    def test_create_execution_plan(self):
        """Test creating an execution plan."""
        plan = ExecutionPlan(
            id="plan-1",
            goal="Test goal",
            steps=[]
        )

        assert plan.id == "plan-1"
        assert plan.goal == "Test goal"
        assert plan.status == TaskStatus.PENDING
        assert len(plan.steps) == 0

    def test_execution_plan_with_steps(self):
        """Test execution plan with steps."""
        steps = [
            TaskStep(id="step-1", description="Step 1"),
            TaskStep(id="step-2", description="Step 2"),
        ]

        plan = ExecutionPlan(
            id="plan-1",
            goal="Test goal",
            steps=steps
        )

        assert len(plan.steps) == 2


class TestEnums:
    """Tests for enum types."""

    def test_task_status_enum(self):
        """Test TaskStatus enum."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    def test_risk_level_enum(self):
        """Test RiskLevel enum."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_tool_category_enum(self):
        """Test ToolCategory enum."""
        assert ToolCategory.CORE.value == "core"
        assert ToolCategory.ENVIRONMENT.value == "environment"
        assert ToolCategory.VERSION_CONTROL.value == "version_control"


class TestTool:
    """Tests for Tool model."""

    def test_create_tool(self):
        """Test creating a tool."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            category=ToolCategory.CORE,
            parameters={"param1": "str"},
            required_params=["param1"]
        )

        assert tool.name == "test_tool"
        assert tool.category == ToolCategory.CORE
        assert tool.risk_level == RiskLevel.LOW
        assert not tool.requires_confirmation

    def test_high_risk_tool(self):
        """Test creating a high-risk tool."""
        tool = Tool(
            name="dangerous_tool",
            description="A dangerous tool",
            category=ToolCategory.CORE,
            parameters={},
            required_params=[],
            risk_level=RiskLevel.HIGH,
            requires_confirmation=True
        )

        assert tool.risk_level == RiskLevel.HIGH
        assert tool.requires_confirmation


class TestContext:
    """Tests for Context model."""

    def test_create_context(self):
        """Test creating a context."""
        context = Context(
            task_id="task-1",
            working_directory="/tmp/test"
        )

        assert context.task_id == "task-1"
        assert context.working_directory == "/tmp/test"
        assert context.environment == {}
        assert context.recent_outputs == []


class TestMessage:
    """Tests for Message model."""

    def test_create_message(self):
        """Test creating a message."""
        message = Message(
            role="user",
            content="Hello"
        )

        assert message.role == "user"
        assert message.content == "Hello"
        assert isinstance(message.timestamp, datetime)


class TestExecutionResult:
    """Tests for ExecutionResult model."""

    def test_successful_result(self):
        """Test successful execution result."""
        result = ExecutionResult(
            success=True,
            output="Success output",
            return_code=0
        )

        assert result.success
        assert result.output == "Success output"
        assert result.return_code == 0
        assert result.error is None

    def test_failed_result(self):
        """Test failed execution result."""
        result = ExecutionResult(
            success=False,
            output="",
            error="Error message",
            return_code=1
        )

        assert not result.success
        assert result.error == "Error message"
        assert result.return_code == 1
