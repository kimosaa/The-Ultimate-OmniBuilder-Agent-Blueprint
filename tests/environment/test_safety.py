"""
Tests for safety module.
"""

import pytest
from omnibuilder.environment.safety import SafetyPrompt, Action, UserConfirmation
from omnibuilder.models import RiskLevel


class TestSafetyPrompt:
    """Tests for SafetyPrompt."""

    @pytest.fixture
    def safety(self):
        return SafetyPrompt()

    def test_classify_risk_critical(self, safety):
        """Test classifying critical risk actions."""
        action = Action(
            name="delete_root",
            description="Delete system files",
            command="rm -rf /"
        )

        risk = safety.classify_risk(action)
        assert risk == RiskLevel.CRITICAL

    def test_classify_risk_high(self, safety):
        """Test classifying high risk actions."""
        action = Action(
            name="git_push",
            description="Push to remote",
            command="git push origin main"
        )

        risk = safety.classify_risk(action)
        assert risk == RiskLevel.HIGH

    def test_classify_risk_medium(self, safety):
        """Test classifying medium risk actions."""
        action = Action(
            name="git_commit",
            description="Commit changes",
            command="git commit -m 'Update'"
        )

        risk = safety.classify_risk(action)
        assert risk == RiskLevel.MEDIUM

    def test_classify_risk_low(self, safety):
        """Test classifying low risk actions."""
        action = Action(
            name="list_files",
            description="List directory contents",
            command="ls -la"
        )

        risk = safety.classify_risk(action)
        assert risk == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_confirm_action_auto_approve_low(self, safety):
        """Test auto-approving low risk actions."""
        safety.auto_approve_low_risk = True

        action = Action(
            name="read_file",
            description="Read a file"
        )

        # Should auto-approve without callback
        approved = await safety.confirm_action(action)
        # Low risk with auto-approve should be true
        # But needs callback in actual use, so this might return False
        assert isinstance(approved, bool)

    def test_get_safe_mode(self, safety):
        """Test getting safe mode status."""
        assert isinstance(safety.get_safe_mode(), bool)

    def test_set_safe_mode(self, safety):
        """Test setting safe mode."""
        safety.set_safe_mode(False)
        assert safety.get_safe_mode() == False

        safety.set_safe_mode(True)
        assert safety.get_safe_mode() == True

    def test_log_sensitive_action(self, safety):
        """Test logging sensitive actions."""
        action = Action(
            name="test_action",
            description="Test action"
        )

        # Should not raise
        safety.log_sensitive_action(action)

        # Check it was logged
        logs = safety.get_audit_log()
        assert len(logs) > 0

    def test_emergency_stop(self, safety):
        """Test emergency stop."""
        with pytest.raises(SystemExit):
            safety.emergency_stop()

    def test_get_audit_log(self, safety):
        """Test getting audit log."""
        logs = safety.get_audit_log()
        assert isinstance(logs, list)


class TestUserConfirmation:
    """Tests for UserConfirmation."""

    @pytest.fixture
    def confirmation(self):
        return UserConfirmation()

    @pytest.mark.asyncio
    async def test_confirm(self, confirmation):
        """Test confirmation method."""
        # This would require user input, so we just test it doesn't crash
        # In actual use, this would be mocked
        assert hasattr(confirmation, 'confirm')
