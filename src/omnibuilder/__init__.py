"""
OmniBuilder - Autonomous Developer, Researcher, and Executor Agent

An autonomous agent capable of planning, building, coding, debugging,
and managing projects end-to-end directly within VS Code and Terminal.
"""

__version__ = "0.1.0"
__author__ = "kimosaa"

from omnibuilder.agent import OmniBuilderAgent
from omnibuilder.config import Config

__all__ = ["OmniBuilderAgent", "Config", "__version__"]
