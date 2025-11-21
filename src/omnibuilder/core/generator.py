"""
P1.7 Code & Artifact Generator

Generates code, documentation, configuration files, and other artifacts.
"""

from typing import Any, Dict, List, Optional
from jinja2 import Template


class CodeSpec:
    """Specification for code generation."""

    def __init__(
        self,
        description: str,
        language: str = "python",
        framework: Optional[str] = None,
        requirements: Optional[List[str]] = None
    ):
        self.description = description
        self.language = language
        self.framework = framework
        self.requirements = requirements or []


class TestSuite:
    """Generated test suite."""

    def __init__(self, tests: List[str], framework: str = "pytest"):
        self.tests = tests
        self.framework = framework


class Documentation:
    """Generated documentation."""

    def __init__(self, content: str, format: str = "markdown"):
        self.content = content
        self.format = format


class CodeGenerator:
    """Generates code from specifications."""

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client
        self._templates: Dict[str, str] = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load code templates."""
        return {
            "python_function": '''def {{ name }}({{ params }}):
    """
    {{ docstring }}
    """
    {{ body }}
''',
            "python_class": '''class {{ name }}:
    """
    {{ docstring }}
    """

    def __init__(self{{ init_params }}):
        {{ init_body }}

    {{ methods }}
''',
            "python_test": '''import pytest

class Test{{ class_name }}:
    """Tests for {{ class_name }}."""

    def test_{{ test_name }}(self):
        """{{ test_description }}"""
        {{ test_body }}
''',
        }

    async def generate_code(
        self,
        spec: CodeSpec,
        language: Optional[str] = None
    ) -> str:
        """
        Generate code from specification.

        Args:
            spec: Code specification
            language: Override language from spec

        Returns:
            Generated code string
        """
        lang = language or spec.language

        if self.llm_client:
            prompt = self._build_code_prompt(spec, lang)
            code = await self.llm_client.complete(prompt)
            return code
        else:
            # Generate basic template code
            return self._generate_template_code(spec, lang)

    def _build_code_prompt(self, spec: CodeSpec, language: str) -> str:
        """Build prompt for code generation."""
        framework_note = ""
        if spec.framework:
            framework_note = f"\nFramework: {spec.framework}"

        requirements_note = ""
        if spec.requirements:
            requirements_note = f"\nRequirements:\n" + "\n".join(f"- {r}" for r in spec.requirements)

        return f"""Generate {language} code for the following:

{spec.description}{framework_note}{requirements_note}

Requirements:
- Write clean, well-documented code
- Include type hints where applicable
- Follow {language} best practices
- Handle errors appropriately

Return only the code, no explanations."""

    def _generate_template_code(self, spec: CodeSpec, language: str) -> str:
        """Generate basic template code when LLM is not available."""
        if language == "python":
            return f'''"""
{spec.description}
"""

def main():
    """Main entry point."""
    # TODO: Implement {spec.description}
    pass

if __name__ == "__main__":
    main()
'''
        else:
            return f"// TODO: Implement {spec.description}"

    async def generate_tests(
        self,
        code: str,
        coverage: str = "full"
    ) -> TestSuite:
        """
        Generate test cases for code.

        Args:
            code: The code to test
            coverage: Coverage level (basic, standard, full)

        Returns:
            TestSuite with generated tests
        """
        if self.llm_client:
            prompt = f"""Generate pytest test cases for this code:

```python
{code}
```

Coverage level: {coverage}

Include:
- Unit tests for each function/method
- Edge case tests
- Error handling tests

Return only the test code."""

            test_code = await self.llm_client.complete(prompt)
            return TestSuite(tests=[test_code])
        else:
            # Generate basic test template
            test_code = '''import pytest

def test_placeholder():
    """Placeholder test - implement actual tests."""
    assert True
'''
            return TestSuite(tests=[test_code])

    async def generate_documentation(self, code: str) -> Documentation:
        """
        Generate documentation for code.

        Args:
            code: The code to document

        Returns:
            Documentation object
        """
        if self.llm_client:
            prompt = f"""Generate documentation for this code:

```python
{code}
```

Include:
- Overview
- Function/class descriptions
- Parameter documentation
- Usage examples
- Return value descriptions

Format as Markdown."""

            doc_content = await self.llm_client.complete(prompt)
            return Documentation(content=doc_content)
        else:
            # Extract basic documentation
            doc = "# Documentation\n\n"
            doc += "## Overview\n\nCode documentation.\n\n"
            doc += "## Details\n\nSee code comments for details.\n"
            return Documentation(content=doc)

    def refactor_code(self, code: str, pattern: str) -> str:
        """
        Apply refactoring pattern to code.

        Args:
            code: Code to refactor
            pattern: Refactoring pattern to apply

        Returns:
            Refactored code
        """
        # Simple pattern-based refactoring
        if pattern == "extract_method":
            # Placeholder - would use AST in production
            return code
        elif pattern == "rename":
            return code
        elif pattern == "inline":
            return code
        else:
            return code


class ArtifactGenerator:
    """Generates configuration files and other artifacts."""

    def __init__(self):
        self._templates: Dict[str, str] = {}

    def generate_config(
        self,
        config_type: str,
        params: Dict[str, Any]
    ) -> str:
        """
        Generate a configuration file.

        Args:
            config_type: Type of config (dockerfile, yaml, json, etc.)
            params: Parameters for the config

        Returns:
            Generated configuration content
        """
        if config_type == "dockerfile":
            return self._generate_dockerfile(params)
        elif config_type == "docker-compose":
            return self._generate_docker_compose(params)
        elif config_type == "github-action":
            return self._generate_github_action(params)
        elif config_type == "gitignore":
            return self._generate_gitignore(params)
        elif config_type == "requirements":
            return self._generate_requirements(params)
        else:
            return f"# Configuration for {config_type}\n"

    def _generate_dockerfile(self, params: Dict[str, Any]) -> str:
        """Generate Dockerfile."""
        base_image = params.get("base_image", "python:3.11-slim")
        workdir = params.get("workdir", "/app")

        return f"""FROM {base_image}

WORKDIR {workdir}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
"""

    def _generate_docker_compose(self, params: Dict[str, Any]) -> str:
        """Generate docker-compose.yml."""
        service_name = params.get("service_name", "app")
        port = params.get("port", 8000)

        return f"""version: '3.8'

services:
  {service_name}:
    build: .
    ports:
      - "{port}:{port}"
    volumes:
      - .:/app
    environment:
      - ENV=development
"""

    def _generate_github_action(self, params: Dict[str, Any]) -> str:
        """Generate GitHub Actions workflow."""
        name = params.get("name", "CI")
        python_version = params.get("python_version", "3.11")

        return f"""name: {name}

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '{python_version}'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run tests
        run: pytest
"""

    def _generate_gitignore(self, params: Dict[str, Any]) -> str:
        """Generate .gitignore."""
        language = params.get("language", "python")

        if language == "python":
            return """__pycache__/
*.py[cod]
.env
venv/
.venv/
dist/
build/
*.egg-info/
.coverage
.pytest_cache/
"""
        else:
            return """# Generated gitignore
node_modules/
.env
dist/
build/
"""

    def _generate_requirements(self, params: Dict[str, Any]) -> str:
        """Generate requirements.txt."""
        packages = params.get("packages", [])
        return "\n".join(packages) if packages else "# Add your dependencies here\n"
