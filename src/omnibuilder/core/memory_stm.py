"""
P1.5 Working Memory (STM) Manager

Manages context within the current session/task, including recent outputs and error logs.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import deque


class ContextItem:
    """An item in the working memory context."""

    def __init__(
        self,
        content: Any,
        item_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.item_type = item_type
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class Output:
    """An output from tool/command execution."""

    def __init__(self, content: str, source: str, success: bool = True):
        self.content = content
        self.source = source
        self.success = success
        self.timestamp = datetime.now()


class Error:
    """An error that occurred during execution."""

    def __init__(self, message: str, source: str, traceback: Optional[str] = None):
        self.message = message
        self.source = source
        self.traceback = traceback
        self.timestamp = datetime.now()


class ContextSummary:
    """Summarized context information."""

    def __init__(
        self,
        task_summary: str,
        recent_actions: List[str],
        key_findings: List[str],
        current_state: str
    ):
        self.task_summary = task_summary
        self.recent_actions = recent_actions
        self.key_findings = key_findings
        self.current_state = current_state


class WorkingMemoryManager:
    """Manages short-term working memory for the current session."""

    def __init__(self, max_items: int = 100, max_outputs: int = 50, max_errors: int = 20):
        self.max_items = max_items
        self.max_outputs = max_outputs
        self.max_errors = max_errors

        self._context_items: deque = deque(maxlen=max_items)
        self._outputs: deque = deque(maxlen=max_outputs)
        self._errors: deque = deque(maxlen=max_errors)
        self._variables: Dict[str, Any] = {}
        self._task_stack: List[str] = []
        self._current_task: Optional[str] = None

    def add_to_context(self, item: ContextItem) -> None:
        """
        Add an item to the current session context.

        Args:
            item: The context item to add
        """
        self._context_items.append(item)

    def add_output(self, content: str, source: str, success: bool = True) -> None:
        """
        Add an execution output to context.

        Args:
            content: Output content
            source: Source of the output (tool name, command, etc.)
            success: Whether the execution was successful
        """
        output = Output(content, source, success)
        self._outputs.append(output)

        # Also add as context item
        self.add_to_context(ContextItem(
            content=content,
            item_type="output",
            metadata={"source": source, "success": success}
        ))

    def add_error(self, message: str, source: str, traceback: Optional[str] = None) -> None:
        """
        Add an error to the error history.

        Args:
            message: Error message
            source: Source of the error
            traceback: Optional traceback string
        """
        error = Error(message, source, traceback)
        self._errors.append(error)

        # Also add as context item
        self.add_to_context(ContextItem(
            content=message,
            item_type="error",
            metadata={"source": source, "traceback": traceback}
        ))

    def get_recent_outputs(self, n: int = 10) -> List[Output]:
        """
        Retrieve recent execution outputs.

        Args:
            n: Number of outputs to retrieve

        Returns:
            List of recent outputs
        """
        return list(self._outputs)[-n:]

    def get_error_history(self) -> List[Error]:
        """
        Get all errors from current session.

        Returns:
            List of errors
        """
        return list(self._errors)

    def get_context_items(self, item_type: Optional[str] = None) -> List[ContextItem]:
        """
        Get context items, optionally filtered by type.

        Args:
            item_type: Optional type to filter by

        Returns:
            List of context items
        """
        items = list(self._context_items)
        if item_type:
            items = [i for i in items if i.item_type == item_type]
        return items

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a session variable.

        Args:
            name: Variable name
            value: Variable value
        """
        self._variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a session variable.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        return self._variables.get(name, default)

    def set_current_task(self, task: str) -> None:
        """
        Set the current task being worked on.

        Args:
            task: Task description
        """
        if self._current_task:
            self._task_stack.append(self._current_task)
        self._current_task = task

    def get_current_task(self) -> Optional[str]:
        """Get the current task."""
        return self._current_task

    def complete_current_task(self) -> Optional[str]:
        """
        Mark current task as complete and return to previous.

        Returns:
            The completed task
        """
        completed = self._current_task
        if self._task_stack:
            self._current_task = self._task_stack.pop()
        else:
            self._current_task = None
        return completed

    def summarize_context(self, max_length: int = 2000) -> ContextSummary:
        """
        Compress context into a summary to fit token limits.

        Args:
            max_length: Maximum character length for summary

        Returns:
            ContextSummary with compressed information
        """
        # Task summary
        task_summary = self._current_task or "No active task"

        # Recent actions (from outputs)
        recent_actions = []
        for output in list(self._outputs)[-5:]:
            action = f"{output.source}: {'success' if output.success else 'failed'}"
            recent_actions.append(action)

        # Key findings (from context items)
        key_findings = []
        for item in list(self._context_items)[-10:]:
            if item.item_type in ["finding", "result", "output"]:
                finding = str(item.content)[:100]
                key_findings.append(finding)

        # Current state
        error_count = len(self._errors)
        output_count = len(self._outputs)
        current_state = f"{output_count} outputs, {error_count} errors"

        return ContextSummary(
            task_summary=task_summary,
            recent_actions=recent_actions,
            key_findings=key_findings,
            current_state=current_state
        )

    def clear_context(self) -> None:
        """Clear all working memory for a new task."""
        self._context_items.clear()
        self._outputs.clear()
        self._errors.clear()
        self._variables.clear()
        self._task_stack.clear()
        self._current_task = None

    def get_token_estimate(self) -> int:
        """
        Estimate the number of tokens in current context.

        Returns:
            Estimated token count
        """
        total_chars = 0

        for item in self._context_items:
            total_chars += len(str(item.content))

        # Rough estimate: ~4 chars per token
        return total_chars // 4

    def export_context(self) -> Dict[str, Any]:
        """
        Export current context for serialization.

        Returns:
            Dictionary of context data
        """
        return {
            "current_task": self._current_task,
            "task_stack": self._task_stack,
            "variables": self._variables,
            "output_count": len(self._outputs),
            "error_count": len(self._errors),
            "context_items": len(self._context_items),
        }

    def import_context(self, data: Dict[str, Any]) -> None:
        """
        Import context from serialized data.

        Args:
            data: Context data to import
        """
        self._current_task = data.get("current_task")
        self._task_stack = data.get("task_stack", [])
        self._variables = data.get("variables", {})
