"""
Tests for configuration module.
"""

import pytest
import tempfile
import os
from pathlib import Path

from omnibuilder.config import Config, LLMConfig, SafetyConfig


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_values(self):
        """Test default LLM configuration."""
        config = LLMConfig()

        assert config.provider == "anthropic"
        assert config.model == "claude-sonnet-4-20250514"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096

    def test_custom_values(self):
        """Test custom LLM configuration."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.5,
            max_tokens=2048
        )

        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048


class TestSafetyConfig:
    """Tests for SafetyConfig."""

    def test_default_values(self):
        """Test default safety configuration."""
        config = SafetyConfig()

        assert config.require_confirmation_high_risk == True
        assert config.safe_mode == True
        assert len(config.blocked_commands) > 0
        assert "rm -rf /" in config.blocked_commands

    def test_custom_blocked_commands(self):
        """Test custom blocked commands."""
        config = SafetyConfig(
            blocked_commands=["custom_dangerous_cmd"]
        )

        assert "custom_dangerous_cmd" in config.blocked_commands


class TestConfig:
    """Tests for main Config."""

    def test_default_config(self):
        """Test default configuration."""
        config = Config()

        assert config.llm.provider == "anthropic"
        assert config.safety.safe_mode == True
        assert config.memory.enable_long_term_memory == True
        assert config.tools.enable_git == True

    def test_save_and_load_yaml(self):
        """Test saving and loading YAML config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")

            # Create and save config
            config = Config()
            config.llm.model = "test-model"
            config.save(config_path)

            # Load config
            loaded = Config.load(config_path)
            assert loaded.llm.model == "test-model"

    def test_save_and_load_toml(self):
        """Test saving and loading TOML config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.toml")

            # Create and save config
            config = Config()
            config.llm.model = "test-model"
            config.save(config_path)

            # Load config
            loaded = Config.load(config_path)
            assert loaded.llm.model == "test-model"

    def test_load_nonexistent(self):
        """Test loading non-existent config returns default."""
        config = Config.load("/nonexistent/config.yaml")
        assert config is not None
        assert config.llm.provider == "anthropic"

    def test_environment_variable_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("OMNIBUILDER_MODEL", "custom-model")

        config = Config.load()
        assert config.llm.api_key == "test-key"
        assert config.llm.model == "custom-model"
