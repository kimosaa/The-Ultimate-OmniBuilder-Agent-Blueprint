"""
Tests for terminal execution agent.
"""

import pytest
from omnibuilder.environment.terminal import TerminalExecutionAgent


class TestTerminalExecutionAgent:
    """Tests for TerminalExecutionAgent."""

    @pytest.fixture
    def terminal(self):
        return TerminalExecutionAgent(safe_mode=True)

    @pytest.fixture
    def terminal_unsafe(self):
        return TerminalExecutionAgent(safe_mode=False)

    @pytest.mark.asyncio
    async def test_execute_shell_simple(self, terminal_unsafe):
        """Test executing a simple command."""
        result = await terminal_unsafe.execute_shell("echo 'hello world'", timeout=5)

        assert result.success
        assert "hello world" in result.output
        assert result.return_code == 0

    @pytest.mark.asyncio
    async def test_execute_shell_with_error(self, terminal_unsafe):
        """Test executing a command that fails."""
        result = await terminal_unsafe.execute_shell("exit 1", timeout=5)

        assert not result.success
        assert result.return_code == 1

    @pytest.mark.asyncio
    async def test_execute_shell_dangerous_blocked(self, terminal):
        """Test that dangerous commands are blocked in safe mode."""
        result = await terminal.execute_shell("rm -rf /", timeout=5)

        assert not result.success
        assert "blocked" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_shell_timeout(self, terminal_unsafe):
        """Test command timeout."""
        result = await terminal_unsafe.execute_shell("sleep 10", timeout=1)

        assert not result.success
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_async(self, terminal_unsafe):
        """Test async command execution."""
        handle = await terminal_unsafe.execute_async("echo 'async test'")

        assert handle.pid > 0
        assert handle.command == "echo 'async test'"

    @pytest.mark.asyncio
    async def test_kill_process(self, terminal_unsafe):
        """Test killing a process."""
        handle = await terminal_unsafe.execute_async("sleep 100")

        killed = terminal_unsafe.kill_process(handle)
        assert killed

    def test_get_environment(self, terminal):
        """Test getting environment variables."""
        env = terminal.get_environment()
        assert isinstance(env, dict)
        assert len(env) > 0

    def test_set_environment(self, terminal):
        """Test setting environment variable."""
        terminal.set_environment("TEST_VAR", "test_value")
        env = terminal.get_environment()
        assert env.get("TEST_VAR") == "test_value"

    def test_unset_environment(self, terminal):
        """Test unsetting environment variable."""
        terminal.set_environment("TEST_VAR", "test_value")
        terminal.unset_environment("TEST_VAR")
        env = terminal.get_environment()
        assert "TEST_VAR" not in env

    @pytest.mark.asyncio
    async def test_run_script_not_found(self, terminal):
        """Test running a non-existent script."""
        result = await terminal.run_script("/nonexistent/script.py")

        assert not result.success
        assert "not found" in result.error.lower()

    def test_get_running_processes(self, terminal):
        """Test getting running processes."""
        processes = terminal.get_running_processes()
        assert isinstance(processes, list)
