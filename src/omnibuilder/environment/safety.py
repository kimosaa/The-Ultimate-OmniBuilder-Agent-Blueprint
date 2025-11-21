"""
P2.6 User Confirmation/Safety Prompt

Requires explicit user confirmation for potentially destructive actions.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from omnibuilder.models import RiskLevel


class Action:
    """An action that may require confirmation."""

    def __init__(
        self,
        name: str,
        description: str,
        command: Optional[str] = None,
        target: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.command = command
        self.target = target
        self.timestamp = datetime.now()


class ApprovalResult:
    """Result of an approval request."""

    def __init__(
        self,
        approved: bool,
        actions: List[Action],
        reason: Optional[str] = None
    ):
        self.approved = approved
        self.actions = actions
        self.reason = reason


class AuditLog:
    """Audit log for sensitive actions."""

    def __init__(self):
        self._entries: List[Dict[str, Any]] = []
        self._logger = logging.getLogger("omnibuilder.audit")

    def log(
        self,
        action: Action,
        risk_level: RiskLevel,
        approved: bool,
        user_response: Optional[str] = None
    ) -> None:
        """Log an action."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action.name,
            "description": action.description,
            "command": action.command,
            "target": action.target,
            "risk_level": risk_level.value,
            "approved": approved,
            "user_response": user_response
        }

        self._entries.append(entry)
        self._logger.info(f"Action: {action.name} | Risk: {risk_level.value} | Approved: {approved}")

    def get_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        return self._entries[-limit:]


class SafetyPrompt:
    """Manages safety prompts and confirmations."""

    def __init__(self, auto_approve_low_risk: bool = True):
        self.auto_approve_low_risk = auto_approve_low_risk
        self._safe_mode = True
        self._audit_log = AuditLog()

        # Risk classification rules
        self._critical_patterns = [
            "rm -rf /",
            "rm -rf /*",
            "mkfs.",
            "dd if=",
            ":(){:|:&};:",
            "chmod -R 777 /",
            "> /dev/sd",
            "git push --force origin main",
            "git push --force origin master",
            "DROP DATABASE",
            "DELETE FROM",
        ]

        self._high_risk_patterns = [
            "rm -rf",
            "rm -r",
            "git push",
            "git reset --hard",
            "git checkout --",
            "sudo ",
            "pip install",
            "npm install -g",
            "docker rm",
            "kubectl delete",
        ]

        self._medium_risk_patterns = [
            "mv ",
            "cp ",
            "git commit",
            "git merge",
            "chmod",
            "chown",
            "pip",
            "npm",
            "apt install",
        ]

    def classify_risk(self, action: Action) -> RiskLevel:
        """
        Classify the risk level of an action.

        Args:
            action: Action to classify

        Returns:
            RiskLevel (low, medium, high, critical)
        """
        # Check command if available
        check_string = ""
        if action.command:
            check_string = action.command.lower()
        else:
            check_string = f"{action.name} {action.description}".lower()

        # Check patterns
        if any(pattern.lower() in check_string for pattern in self._critical_patterns):
            return RiskLevel.CRITICAL

        if any(pattern.lower() in check_string for pattern in self._high_risk_patterns):
            return RiskLevel.HIGH

        if any(pattern.lower() in check_string for pattern in self._medium_risk_patterns):
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    async def confirm_action(
        self,
        action: Action,
        callback: Optional[callable] = None
    ) -> bool:
        """
        Request user confirmation for an action.

        Args:
            action: Action to confirm
            callback: Optional callback for getting user input

        Returns:
            True if approved
        """
        risk_level = self.classify_risk(action)

        # Auto-approve low risk if enabled
        if risk_level == RiskLevel.LOW and self.auto_approve_low_risk:
            self._audit_log.log(action, risk_level, True, "auto-approved")
            return True

        # Always require confirmation for critical actions
        if risk_level == RiskLevel.CRITICAL:
            print(f"\n{'='*60}")
            print("⚠️  CRITICAL RISK ACTION - REQUIRES EXPLICIT CONFIRMATION")
            print(f"{'='*60}")
        elif risk_level == RiskLevel.HIGH:
            print(f"\n{'='*50}")
            print("⚠️  HIGH RISK ACTION")
            print(f"{'='*50}")
        else:
            print(f"\n{'='*40}")
            print("Action requires confirmation")
            print(f"{'='*40}")

        print(f"Action: {action.name}")
        print(f"Description: {action.description}")
        if action.command:
            print(f"Command: {action.command}")
        if action.target:
            print(f"Target: {action.target}")
        print(f"Risk Level: {risk_level.value.upper()}")
        print()

        # Get user confirmation
        if callback:
            approved = await callback(action, risk_level)
        else:
            # Default: use input()
            response = input("Approve this action? (yes/no): ").strip().lower()
            approved = response in ["yes", "y"]

        self._audit_log.log(action, risk_level, approved)
        return approved

    async def require_approval(self, actions: List[Action]) -> ApprovalResult:
        """
        Request approval for multiple actions.

        Args:
            actions: List of actions to approve

        Returns:
            ApprovalResult with approval status
        """
        if not actions:
            return ApprovalResult(approved=True, actions=[])

        # Check if any action is high risk or above
        risk_levels = [self.classify_risk(a) for a in actions]
        max_risk = max(risk_levels, key=lambda r: list(RiskLevel).index(r))

        if max_risk in [RiskLevel.LOW] and self.auto_approve_low_risk:
            for action in actions:
                self._audit_log.log(action, RiskLevel.LOW, True, "batch-auto-approved")
            return ApprovalResult(approved=True, actions=actions)

        print(f"\nBatch approval request for {len(actions)} actions:")
        for i, action in enumerate(actions, 1):
            risk = self.classify_risk(action)
            print(f"  {i}. [{risk.value}] {action.name}: {action.description}")

        response = input("\nApprove all actions? (yes/no): ").strip().lower()
        approved = response in ["yes", "y"]

        for action in actions:
            risk = self.classify_risk(action)
            self._audit_log.log(action, risk, approved, "batch")

        return ApprovalResult(
            approved=approved,
            actions=actions,
            reason="User batch approval" if approved else "User rejected"
        )

    def log_sensitive_action(self, action: Action) -> None:
        """
        Log a sensitive action without requiring confirmation.

        Args:
            action: Action to log
        """
        risk_level = self.classify_risk(action)
        self._audit_log.log(action, risk_level, True, "logged-only")

    def get_safe_mode(self) -> bool:
        """Check if safe mode is enabled."""
        return self._safe_mode

    def set_safe_mode(self, enabled: bool) -> None:
        """Enable or disable safe mode."""
        self._safe_mode = enabled

    def emergency_stop(self) -> None:
        """
        Immediately halt all operations.

        Raises:
            SystemExit: To stop all execution
        """
        print("\n🛑 EMERGENCY STOP ACTIVATED")
        print("All operations halted.")

        # Log the emergency stop
        action = Action(
            name="emergency_stop",
            description="Emergency stop activated by user"
        )
        self._audit_log.log(action, RiskLevel.CRITICAL, False, "emergency")

        raise SystemExit("Emergency stop activated")

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get the audit log entries."""
        return self._audit_log.get_entries()


class UserConfirmation:
    """Simplified confirmation interface."""

    def __init__(self):
        self._safety = SafetyPrompt()

    async def confirm(self, message: str, risk: str = "medium") -> bool:
        """
        Simple confirmation prompt.

        Args:
            message: Confirmation message
            risk: Risk level string

        Returns:
            True if confirmed
        """
        risk_map = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL
        }

        action = Action(
            name="user_confirmation",
            description=message
        )

        return await self._safety.confirm_action(action)

    def require(self, message: str) -> bool:
        """
        Synchronous confirmation (blocking).

        Args:
            message: Confirmation message

        Returns:
            True if confirmed
        """
        print(f"\nConfirmation required: {message}")
        response = input("Proceed? (yes/no): ").strip().lower()
        return response in ["yes", "y"]
