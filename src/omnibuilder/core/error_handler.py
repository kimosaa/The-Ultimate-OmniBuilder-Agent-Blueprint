"""
P1.6 Self-Correction & Error Handler

Analyzes tool/code execution failures and regenerates new plans or actions.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from omnibuilder.models import ErrorAnalysis, RiskLevel


class FixPlan:
    """A plan to fix an error."""

    def __init__(self, steps: List[str], confidence: float):
        self.steps = steps
        self.confidence = confidence
        self.created_at = datetime.now()


class RollbackResult:
    """Result of a rollback operation."""

    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base


class ErrorHandler:
    """Handles errors and generates recovery strategies."""

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client
        self._error_patterns: Dict[str, List[str]] = {}
        self._successful_fixes: List[Dict[str, Any]] = []

    def analyze_error(self, error: Exception, context: Optional[Dict] = None) -> ErrorAnalysis:
        """
        Analyze an error to determine root cause.

        Args:
            error: The exception that occurred
            context: Optional execution context

        Returns:
            ErrorAnalysis with diagnosis
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Classify severity
        severity = self._classify_severity(error_type, error_message)

        # Find root cause
        root_cause = self._identify_root_cause(error_type, error_message, context)

        # Generate suggested fixes
        suggested_fixes = self._generate_fix_suggestions(error_type, error_message)

        # Find related errors
        related = self._find_related_errors(error_type)

        return ErrorAnalysis(
            error_type=error_type,
            root_cause=root_cause,
            suggested_fixes=suggested_fixes,
            related_errors=related,
            severity=severity
        )

    def _classify_severity(self, error_type: str, message: str) -> RiskLevel:
        """Classify error severity."""
        critical_types = ["SystemExit", "KeyboardInterrupt", "MemoryError"]
        high_types = ["PermissionError", "FileNotFoundError", "ConnectionError"]
        medium_types = ["ValueError", "TypeError", "KeyError"]

        if error_type in critical_types:
            return RiskLevel.CRITICAL
        elif error_type in high_types:
            return RiskLevel.HIGH
        elif error_type in medium_types:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _identify_root_cause(
        self,
        error_type: str,
        message: str,
        context: Optional[Dict]
    ) -> str:
        """Identify the root cause of an error."""
        # Common patterns
        if "No such file" in message or "FileNotFoundError" in error_type:
            return "File or directory does not exist"
        elif "Permission denied" in message:
            return "Insufficient permissions to access resource"
        elif "Connection" in message or "Timeout" in message:
            return "Network connectivity or timeout issue"
        elif "Import" in error_type or "Module" in message:
            return "Missing or incompatible dependency"
        elif "Syntax" in error_type:
            return "Invalid syntax in code"
        elif "Key" in error_type or "Index" in error_type:
            return "Invalid key or index access"
        elif "Type" in error_type:
            return "Type mismatch or invalid operation"
        else:
            return f"Error of type {error_type}: {message[:100]}"

    def _generate_fix_suggestions(self, error_type: str, message: str) -> List[str]:
        """Generate suggestions to fix the error."""
        suggestions = []

        if "FileNotFoundError" in error_type:
            suggestions = [
                "Check if the file path is correct",
                "Ensure the file exists before accessing",
                "Create the file or directory if needed",
            ]
        elif "PermissionError" in error_type:
            suggestions = [
                "Check file/directory permissions",
                "Run with appropriate privileges",
                "Verify ownership of the resource",
            ]
        elif "ConnectionError" in error_type or "Timeout" in message:
            suggestions = [
                "Check network connectivity",
                "Verify the service is running",
                "Increase timeout value",
                "Retry the operation",
            ]
        elif "ImportError" in error_type or "ModuleNotFoundError" in error_type:
            suggestions = [
                "Install the missing package",
                "Check the import statement",
                "Verify virtual environment is activated",
            ]
        elif "SyntaxError" in error_type:
            suggestions = [
                "Check for missing brackets, quotes, or colons",
                "Verify indentation is correct",
                "Review the syntax of the statement",
            ]
        elif "TypeError" in error_type:
            suggestions = [
                "Check the types of variables",
                "Verify function arguments",
                "Add type conversion if needed",
            ]
        else:
            suggestions = [
                f"Review the {error_type} documentation",
                "Check the error message for details",
                "Add error handling around the operation",
            ]

        return suggestions

    def _find_related_errors(self, error_type: str) -> List[str]:
        """Find related error patterns."""
        related_map = {
            "FileNotFoundError": ["PermissionError", "IsADirectoryError"],
            "ConnectionError": ["TimeoutError", "ConnectionRefusedError"],
            "ImportError": ["ModuleNotFoundError", "AttributeError"],
            "ValueError": ["TypeError", "KeyError"],
        }

        return related_map.get(error_type, [])

    async def generate_fix(
        self,
        error: Exception,
        context: Optional[Dict] = None
    ) -> FixPlan:
        """
        Generate a fix plan for an error.

        Args:
            error: The error to fix
            context: Execution context

        Returns:
            FixPlan with steps to resolve
        """
        analysis = self.analyze_error(error, context)

        # Start with suggested fixes
        steps = analysis.suggested_fixes.copy()

        # Add verification step
        steps.append("Verify the fix resolved the issue")

        # Calculate confidence based on severity and pattern matching
        confidence = 0.7
        if analysis.severity == RiskLevel.LOW:
            confidence = 0.9
        elif analysis.severity == RiskLevel.CRITICAL:
            confidence = 0.3

        return FixPlan(steps=steps, confidence=confidence)

    def learn_from_error(
        self,
        error: Exception,
        fix: FixPlan,
        success: bool
    ) -> None:
        """
        Store error pattern for future avoidance.

        Args:
            error: The error that occurred
            fix: The fix that was applied
            success: Whether the fix worked
        """
        error_type = type(error).__name__

        if error_type not in self._error_patterns:
            self._error_patterns[error_type] = []

        self._error_patterns[error_type].append(str(error))

        if success:
            self._successful_fixes.append({
                "error_type": error_type,
                "error_message": str(error),
                "fix_steps": fix.steps,
                "timestamp": datetime.now().isoformat()
            })


class SelfCorrector:
    """Self-correction mechanism with retry logic."""

    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()
        self._action_history: List[Dict[str, Any]] = []

    async def retry_with_backoff(
        self,
        action: callable,
        config: Optional[RetryConfig] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry an action with exponential backoff.

        Args:
            action: The action to retry
            config: Retry configuration
            *args: Arguments for the action
            **kwargs: Keyword arguments for the action

        Returns:
            Result of the action

        Raises:
            Exception: If all retries fail
        """
        config = config or RetryConfig()

        last_error = None
        delay = config.initial_delay

        for attempt in range(config.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(action):
                    result = await action(*args, **kwargs)
                else:
                    result = action(*args, **kwargs)

                # Success - record and return
                self._record_action(action.__name__, True, attempt)
                return result

            except Exception as e:
                last_error = e

                if attempt < config.max_retries:
                    # Wait before retrying
                    await asyncio.sleep(delay)
                    delay = min(
                        delay * config.exponential_base,
                        config.max_delay
                    )

        # All retries failed
        self._record_action(action.__name__, False, config.max_retries)
        raise last_error

    def _record_action(self, name: str, success: bool, attempts: int) -> None:
        """Record action execution for history."""
        self._action_history.append({
            "action": name,
            "success": success,
            "attempts": attempts,
            "timestamp": datetime.now().isoformat()
        })

    async def rollback_action(self, action_id: str) -> RollbackResult:
        """
        Rollback a failed action.

        Args:
            action_id: ID of the action to rollback

        Returns:
            RollbackResult indicating success/failure
        """
        # This would be implemented based on the specific action types
        # For now, return a placeholder
        return RollbackResult(
            success=False,
            message="Rollback not implemented for this action type"
        )

    def get_action_history(self) -> List[Dict[str, Any]]:
        """Get history of actions and their outcomes."""
        return self._action_history.copy()
