"""
Environment and Interface Functions - Terminal & VS Code Compatibility
"""

from omnibuilder.environment.codebase import CodebaseContextProvider
from omnibuilder.environment.terminal import TerminalExecutionAgent
from omnibuilder.environment.filesystem import FileSystemManager, DiffPatchTool
from omnibuilder.environment.local_llm import LocalInferenceHandler
from omnibuilder.environment.ide import IDEToolInvocation
from omnibuilder.environment.safety import SafetyPrompt, UserConfirmation

__all__ = [
    "CodebaseContextProvider",
    "TerminalExecutionAgent",
    "FileSystemManager",
    "DiffPatchTool",
    "LocalInferenceHandler",
    "IDEToolInvocation",
    "SafetyPrompt",
    "UserConfirmation",
]
