"""
Configuration management for OmniBuilder.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import yaml
import toml
from dotenv import load_dotenv


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = "anthropic"  # anthropic, openai, ollama, lmstudio
    model: str = "claude-sonnet-4-20250514"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120


class SafetyConfig(BaseModel):
    """Safety and confirmation settings."""
    require_confirmation_high_risk: bool = True
    require_confirmation_critical: bool = True
    safe_mode: bool = True
    allowed_directories: list[str] = Field(default_factory=list)
    blocked_commands: list[str] = Field(
        default_factory=lambda: [
            "rm -rf /",
            "rm -rf /*",
            "mkfs",
            ":(){:|:&};:",
            "dd if=/dev/zero",
        ]
    )
    max_execution_time: int = 300  # seconds


class MemoryConfig(BaseModel):
    """Memory and storage settings."""
    enable_long_term_memory: bool = True
    memory_db_path: str = ".omnibuilder/memory"
    vector_db_path: str = ".omnibuilder/vectors"
    max_context_tokens: int = 100000
    max_history_messages: int = 50


class ToolsConfig(BaseModel):
    """External tools configuration."""
    enable_web_search: bool = True
    enable_git: bool = True
    enable_docker: bool = False
    enable_cloud: bool = False
    git_auto_commit: bool = False
    git_sign_commits: bool = False


class Config(BaseModel):
    """Main configuration for OmniBuilder."""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)

    # General settings
    working_directory: str = "."
    log_level: str = "INFO"
    log_file: Optional[str] = ".omnibuilder/logs/agent.log"
    verbose: bool = False

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from file and environment."""
        # Load .env file
        load_dotenv()

        config_data: Dict[str, Any] = {}

        # Load from file if provided
        if config_path:
            path = Path(config_path)
            if path.exists():
                if path.suffix in [".yaml", ".yml"]:
                    with open(path) as f:
                        config_data = yaml.safe_load(f)
                elif path.suffix == ".toml":
                    with open(path) as f:
                        config_data = toml.load(f)
        else:
            # Try default locations
            for default_path in [
                ".omnibuilder/config.yaml",
                ".omnibuilder/config.toml",
                "omnibuilder.yaml",
                "omnibuilder.toml",
            ]:
                if Path(default_path).exists():
                    return cls.load(default_path)

        # Override with environment variables
        config = cls(**config_data)

        # LLM API keys from environment
        if os.getenv("ANTHROPIC_API_KEY"):
            config.llm.api_key = os.getenv("ANTHROPIC_API_KEY")
        elif os.getenv("OPENAI_API_KEY"):
            config.llm.api_key = os.getenv("OPENAI_API_KEY")
            config.llm.provider = "openai"

        # Override model if set
        if os.getenv("OMNIBUILDER_MODEL"):
            config.llm.model = os.getenv("OMNIBUILDER_MODEL")

        return config

    def save(self, config_path: str) -> None:
        """Save configuration to file."""
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix in [".yaml", ".yml"]:
            with open(path, "w") as f:
                yaml.dump(self.model_dump(), f, default_flow_style=False)
        elif path.suffix == ".toml":
            with open(path, "w") as f:
                toml.dump(self.model_dump(), f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")


def get_default_config() -> Config:
    """Get default configuration."""
    return Config.load()
