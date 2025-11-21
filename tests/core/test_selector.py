"""
Tests for the core selector module.
"""

import pytest
from omnibuilder.core.selector import ToolSelector
from omnibuilder.models import Tool, ToolCategory, RiskLevel, Context


class TestToolSelector:
    """Tests for ToolSelector."""

    @pytest.fixture
    def selector(self):
        return ToolSelector()

    @pytest.fixture
    def context(self):
        return Context(
            task_id="test-task",
            working_directory="/tmp/test"
        )

    def test_initialization(self, selector):
        """Test selector initializes with default tools."""
        tools = selector.list_tools()
        assert len(tools) > 0
        assert any(t.name == "execute_shell" for t in tools)
        assert any(t.name == "read_file" for t in tools)

    def test_register_tool(self, selector):
        """Test registering a new tool."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            category=ToolCategory.CORE,
            parameters={"param1": "str"},
            required_params=["param1"]
        )

        selector.register_tool(tool)
        assert selector.get_tool("test_tool") == tool

    def test_get_tool(self, selector):
        """Test getting a tool by name."""
        tool = selector.get_tool("execute_shell")
        assert tool is not None
        assert tool.name == "execute_shell"

    def test_list_tools_all(self, selector):
        """Test listing all tools."""
        tools = selector.list_tools()
        assert len(tools) > 0

    def test_list_tools_by_category(self, selector):
        """Test listing tools by category."""
        env_tools = selector.list_tools(category=ToolCategory.ENVIRONMENT)
        assert all(t.category == ToolCategory.ENVIRONMENT for t in env_tools)

    @pytest.mark.asyncio
    async def test_select_tool_shell_command(self, selector, context):
        """Test selecting tool for shell command."""
        tool = await selector.select_tool(context, "run npm install")
        assert tool is not None
        assert tool.name == "execute_shell"

    @pytest.mark.asyncio
    async def test_select_tool_file_read(self, selector, context):
        """Test selecting tool for file reading."""
        tool = await selector.select_tool(context, "read the config file")
        assert tool is not None
        assert tool.name == "read_file"

    @pytest.mark.asyncio
    async def test_select_tool_no_match(self, selector, context):
        """Test selecting tool with no clear match."""
        tool = await selector.select_tool(context, "xyz abc 123")
        # Should return None or a fallback
        assert tool is None or tool.name

    def test_validate_tool_params_valid(self, selector):
        """Test validating valid parameters."""
        tool = selector.get_tool("execute_shell")
        params = {"command": "echo hello"}

        result = selector.validate_tool_params(tool, params)
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_tool_params_missing_required(self, selector):
        """Test validation with missing required parameters."""
        tool = selector.get_tool("execute_shell")
        params = {}

        result = selector.validate_tool_params(tool, params)
        assert not result.valid
        assert len(result.errors) > 0

    def test_validate_tool_params_wrong_type(self, selector):
        """Test validation with wrong parameter type."""
        tool = selector.get_tool("execute_shell")
        params = {"command": 123}  # Should be string

        result = selector.validate_tool_params(tool, params)
        assert not result.valid

    def test_get_tool_alternatives(self, selector):
        """Test getting alternative tools."""
        tool = selector.get_tool("execute_shell")
        alternatives = selector.get_tool_alternatives(tool)

        # Should find other environment tools
        assert all(alt.category == tool.category for alt in alternatives)
        assert all(alt.name != tool.name for alt in alternatives)

    def test_estimate_tool_cost(self, selector):
        """Test estimating tool cost."""
        tool = selector.get_tool("execute_shell")
        params = {"command": "echo hello", "timeout": 10}

        cost = selector.estimate_tool_cost(tool, params)
        assert cost.time_seconds > 0
        assert cost.risk == tool.risk_level
