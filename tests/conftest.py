"""
Shared test fixtures and utilities.
"""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_file():
    """Create a temporary file for tests."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return '''
def hello(name):
    """Say hello."""
    return f"Hello, {name}!"

class Calculator:
    """A simple calculator."""

    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
'''


@pytest.fixture
def sample_config_yaml():
    """Sample YAML configuration."""
    return '''
llm:
  provider: anthropic
  model: claude-sonnet-4
  temperature: 0.7

safety:
  safe_mode: true
  require_confirmation_high_risk: true

tools:
  enable_git: true
  enable_docker: false
'''


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
