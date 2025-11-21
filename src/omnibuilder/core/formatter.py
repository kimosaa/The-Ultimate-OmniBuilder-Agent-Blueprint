"""
P1.8 Output & Format Generator

Formats final responses and actions for the user or execution environment.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime


class FormattedOutput:
    """A formatted output for display."""

    def __init__(self, content: str, format_type: str = "text"):
        self.content = content
        self.format_type = format_type
        self.timestamp = datetime.now()


class Summary:
    """Summary of execution results."""

    def __init__(
        self,
        title: str,
        overview: str,
        details: List[str],
        status: str
    ):
        self.title = title
        self.overview = overview
        self.details = details
        self.status = status


class DiffOutput:
    """Formatted diff output."""

    def __init__(self, diff_text: str, additions: int, deletions: int):
        self.diff_text = diff_text
        self.additions = additions
        self.deletions = deletions


class OutputFormatter:
    """Formats outputs for different contexts."""

    def __init__(self):
        self._color_enabled = True

    def format_response(
        self,
        content: Any,
        format_type: str = "text"
    ) -> FormattedOutput:
        """
        Format content for user display.

        Args:
            content: Content to format
            format_type: Output format (text, json, markdown, table)

        Returns:
            FormattedOutput ready for display
        """
        if format_type == "json":
            formatted = self._format_json(content)
        elif format_type == "markdown":
            formatted = self._format_markdown(content)
        elif format_type == "table":
            formatted = self._format_table(content)
        else:
            formatted = self._format_text(content)

        return FormattedOutput(content=formatted, format_type=format_type)

    def _format_text(self, content: Any) -> str:
        """Format as plain text."""
        if isinstance(content, str):
            return content
        elif isinstance(content, (list, tuple)):
            return "\n".join(str(item) for item in content)
        elif isinstance(content, dict):
            lines = []
            for key, value in content.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        else:
            return str(content)

    def _format_json(self, content: Any) -> str:
        """Format as JSON."""
        try:
            if isinstance(content, str):
                # Check if it's already JSON
                json.loads(content)
                return content
            return json.dumps(content, indent=2, default=str)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"content": str(content)}, indent=2)

    def _format_markdown(self, content: Any) -> str:
        """Format as Markdown."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            return "\n".join(f"- {item}" for item in content)
        elif isinstance(content, dict):
            lines = []
            for key, value in content.items():
                lines.append(f"**{key}**: {value}")
            return "\n".join(lines)
        else:
            return str(content)

    def _format_table(self, content: Any) -> str:
        """Format as ASCII table."""
        if not isinstance(content, list) or not content:
            return self._format_text(content)

        # Assume list of dicts
        if not isinstance(content[0], dict):
            return "\n".join(str(item) for item in content)

        headers = list(content[0].keys())
        rows = [[str(row.get(h, "")) for h in headers] for row in content]

        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))

        # Build table
        sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
        header_row = "|" + "|".join(f" {h:<{widths[i]}} " for i, h in enumerate(headers)) + "|"

        table_lines = [sep, header_row, sep]
        for row in rows:
            row_str = "|" + "|".join(f" {cell:<{widths[i]}} " for i, cell in enumerate(row)) + "|"
            table_lines.append(row_str)
        table_lines.append(sep)

        return "\n".join(table_lines)

    def format_for_tool(self, content: Any, tool_name: str) -> Dict[str, Any]:
        """
        Format content for tool consumption.

        Args:
            content: Content to format
            tool_name: Name of the target tool

        Returns:
            Formatted input for the tool
        """
        # Default: pass through as parameters
        if isinstance(content, dict):
            return content
        elif isinstance(content, str):
            return {"input": content}
        else:
            return {"data": content}

    def generate_summary(
        self,
        results: List[Dict[str, Any]],
        title: Optional[str] = None
    ) -> Summary:
        """
        Create an execution summary.

        Args:
            results: List of execution results
            title: Optional title for the summary

        Returns:
            Summary object
        """
        if not results:
            return Summary(
                title=title or "Execution Summary",
                overview="No results to summarize",
                details=[],
                status="empty"
            )

        # Count successes/failures
        successes = sum(1 for r in results if r.get("success", False))
        failures = len(results) - successes

        # Generate overview
        overview = f"Completed {len(results)} operations: {successes} succeeded, {failures} failed"

        # Generate details
        details = []
        for i, result in enumerate(results, 1):
            status = "success" if result.get("success") else "failed"
            detail = f"{i}. {result.get('operation', 'Unknown')}: {status}"
            if result.get("message"):
                detail += f" - {result['message']}"
            details.append(detail)

        # Overall status
        if failures == 0:
            status = "success"
        elif successes == 0:
            status = "failed"
        else:
            status = "partial"

        return Summary(
            title=title or "Execution Summary",
            overview=overview,
            details=details,
            status=status
        )

    def format_diff(self, old: str, new: str) -> DiffOutput:
        """
        Generate readable diff output.

        Args:
            old: Original content
            new: Modified content

        Returns:
            DiffOutput with formatted diff
        """
        import difflib

        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile="original",
            tofile="modified"
        )

        diff_text = "".join(diff)

        # Count changes
        additions = sum(1 for line in diff_text.split("\n") if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff_text.split("\n") if line.startswith("-") and not line.startswith("---"))

        return DiffOutput(
            diff_text=diff_text,
            additions=additions,
            deletions=deletions
        )

    def export_artifact(
        self,
        artifact: Any,
        format_type: str = "json"
    ) -> str:
        """
        Export artifact to file format.

        Args:
            artifact: Artifact to export
            format_type: Export format

        Returns:
            Formatted content for file
        """
        if format_type == "json":
            return json.dumps(artifact, indent=2, default=str)
        elif format_type == "yaml":
            import yaml
            return yaml.dump(artifact, default_flow_style=False)
        elif format_type == "csv":
            if isinstance(artifact, list) and artifact:
                if isinstance(artifact[0], dict):
                    headers = list(artifact[0].keys())
                    lines = [",".join(headers)]
                    for item in artifact:
                        lines.append(",".join(str(item.get(h, "")) for h in headers))
                    return "\n".join(lines)
            return str(artifact)
        else:
            return str(artifact)

    def format_error(
        self,
        error: Exception,
        include_traceback: bool = False
    ) -> str:
        """
        Format an error for display.

        Args:
            error: The error to format
            include_traceback: Whether to include full traceback

        Returns:
            Formatted error string
        """
        error_type = type(error).__name__
        error_msg = str(error)

        formatted = f"Error ({error_type}): {error_msg}"

        if include_traceback:
            import traceback
            tb = traceback.format_exc()
            formatted += f"\n\nTraceback:\n{tb}"

        return formatted

    def format_progress(
        self,
        current: int,
        total: int,
        message: str = ""
    ) -> str:
        """
        Format progress indicator.

        Args:
            current: Current progress
            total: Total items
            message: Optional message

        Returns:
            Formatted progress string
        """
        percentage = (current / total * 100) if total > 0 else 0
        bar_width = 20
        filled = int(bar_width * current / total) if total > 0 else 0
        bar = "=" * filled + "-" * (bar_width - filled)

        progress = f"[{bar}] {percentage:.1f}% ({current}/{total})"
        if message:
            progress += f" - {message}"

        return progress
