"""
P2.2 Terminal Execution Agent

Executes shell commands safely and captures output/status.
"""

import asyncio
import os
import shlex
import signal
import subprocess
from typing import AsyncIterator, Callable, Dict, List, Optional

from omnibuilder.models import ExecutionResult


class ProcessHandle:
    """Handle for a running process."""

    def __init__(self, process: asyncio.subprocess.Process, command: str):
        self.process = process
        self.command = command
        self.pid = process.pid
        self.started_at = asyncio.get_event_loop().time()
        self._output_buffer: List[str] = []

    @property
    def is_running(self) -> bool:
        """Check if process is still running."""
        return self.process.returncode is None


class TerminalExecutionAgent:
    """Executes shell commands safely with output capture."""

    def __init__(self, safe_mode: bool = True, working_dir: Optional[str] = None):
        self.safe_mode = safe_mode
        self.working_dir = working_dir or os.getcwd()
        self._environment = os.environ.copy()
        self._running_processes: Dict[int, ProcessHandle] = {}

        # Commands that require confirmation in safe mode
        self._dangerous_patterns = [
            "rm -rf", "rm -fr", "rmdir", "> /dev/",
            "mkfs", "dd if=", "chmod -R 777",
            ":(){ :|:& };:", "wget", "curl | sh",
            "git push --force", "git reset --hard",
        ]

    async def execute_shell(
        self,
        command: str,
        timeout: int = 30,
        cwd: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute a shell command.

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds
            cwd: Working directory

        Returns:
            ExecutionResult with output and status
        """
        # Safety check
        if self.safe_mode and self._is_dangerous(command):
            return ExecutionResult(
                success=False,
                output="",
                error=f"Command blocked by safe mode: {command}",
                return_code=-1
            )

        work_dir = cwd or self.working_dir
        start_time = asyncio.get_event_loop().time()

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=self._environment
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            duration = asyncio.get_event_loop().time() - start_time

            return ExecutionResult(
                success=process.returncode == 0,
                output=stdout.decode('utf-8', errors='replace'),
                error=stderr.decode('utf-8', errors='replace') if stderr else None,
                return_code=process.returncode,
                duration=duration
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                return_code=-1,
                duration=timeout
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                return_code=-1
            )

    def _is_dangerous(self, command: str) -> bool:
        """Check if command matches dangerous patterns."""
        command_lower = command.lower()
        return any(pattern in command_lower for pattern in self._dangerous_patterns)

    async def execute_async(
        self,
        command: str,
        callback: Optional[Callable[[str], None]] = None
    ) -> ProcessHandle:
        """
        Execute command asynchronously.

        Args:
            command: Command to execute
            callback: Callback for output lines

        Returns:
            ProcessHandle for the running process
        """
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir,
            env=self._environment
        )

        handle = ProcessHandle(process, command)
        self._running_processes[process.pid] = handle

        # Start output reading if callback provided
        if callback:
            asyncio.create_task(self._read_output(handle, callback))

        return handle

    async def _read_output(
        self,
        handle: ProcessHandle,
        callback: Callable[[str], None]
    ) -> None:
        """Read output from process and call callback."""
        while handle.is_running:
            if handle.process.stdout:
                line = await handle.process.stdout.readline()
                if line:
                    decoded = line.decode('utf-8', errors='replace')
                    handle._output_buffer.append(decoded)
                    callback(decoded)
                else:
                    await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.1)

    async def stream_output(self, handle: ProcessHandle) -> AsyncIterator[str]:
        """
        Stream output from a running process.

        Args:
            handle: Process handle

        Yields:
            Output lines
        """
        while handle.is_running or handle._output_buffer:
            if handle._output_buffer:
                yield handle._output_buffer.pop(0)
            else:
                if handle.process.stdout:
                    line = await handle.process.stdout.readline()
                    if line:
                        yield line.decode('utf-8', errors='replace')
                    else:
                        await asyncio.sleep(0.1)
                else:
                    await asyncio.sleep(0.1)

    def kill_process(self, handle: ProcessHandle) -> bool:
        """
        Terminate a running process.

        Args:
            handle: Process handle

        Returns:
            True if killed successfully
        """
        try:
            if handle.is_running:
                handle.process.terminate()
                # Give it a moment to terminate gracefully
                try:
                    handle.process.wait()
                except Exception:
                    handle.process.kill()

            if handle.pid in self._running_processes:
                del self._running_processes[handle.pid]

            return True
        except Exception:
            return False

    def get_environment(self) -> Dict[str, str]:
        """Get current environment variables."""
        return self._environment.copy()

    def set_environment(self, key: str, value: str) -> None:
        """
        Set an environment variable.

        Args:
            key: Variable name
            value: Variable value
        """
        self._environment[key] = value

    def unset_environment(self, key: str) -> None:
        """Remove an environment variable."""
        if key in self._environment:
            del self._environment[key]

    async def run_script(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        timeout: int = 60
    ) -> ExecutionResult:
        """
        Run a script file.

        Args:
            script_path: Path to the script
            args: Script arguments
            timeout: Timeout in seconds

        Returns:
            ExecutionResult
        """
        if not os.path.exists(script_path):
            return ExecutionResult(
                success=False,
                output="",
                error=f"Script not found: {script_path}",
                return_code=-1
            )

        # Determine interpreter based on extension
        ext = os.path.splitext(script_path)[1].lower()
        if ext == '.py':
            command = f"python {shlex.quote(script_path)}"
        elif ext == '.sh':
            command = f"bash {shlex.quote(script_path)}"
        elif ext == '.js':
            command = f"node {shlex.quote(script_path)}"
        else:
            command = shlex.quote(script_path)

        if args:
            command += " " + " ".join(shlex.quote(arg) for arg in args)

        return await self.execute_shell(command, timeout=timeout)

    def get_running_processes(self) -> List[ProcessHandle]:
        """Get list of running processes."""
        return [h for h in self._running_processes.values() if h.is_running]

    async def wait_for_process(
        self,
        handle: ProcessHandle,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Wait for a process to complete.

        Args:
            handle: Process handle
            timeout: Optional timeout

        Returns:
            ExecutionResult
        """
        try:
            if timeout:
                await asyncio.wait_for(handle.process.wait(), timeout)
            else:
                await handle.process.wait()

            stdout = await handle.process.stdout.read() if handle.process.stdout else b""
            stderr = await handle.process.stderr.read() if handle.process.stderr else b""

            return ExecutionResult(
                success=handle.process.returncode == 0,
                output=stdout.decode('utf-8', errors='replace'),
                error=stderr.decode('utf-8', errors='replace') if stderr else None,
                return_code=handle.process.returncode
            )
        except asyncio.TimeoutError:
            self.kill_process(handle)
            return ExecutionResult(
                success=False,
                output="",
                error="Process timed out",
                return_code=-1
            )
