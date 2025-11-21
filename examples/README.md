# OmniBuilder Examples

This directory contains example projects demonstrating OmniBuilder's capabilities.

## Examples Overview

| Example | Description | Difficulty | Features Demonstrated |
|---------|-------------|------------|----------------------|
| **hello_world** | Multi-language Hello World | Beginner | Basic code generation, file creation |
| **rest_api** | FastAPI REST API | Intermediate | API design, database, auth, full stack |
| **data_analysis** | CSV analysis with visualizations | Intermediate | Data processing, charting, reporting |
| **microservice** | Docker microservice | Advanced | Docker, cloud deployment, CI/CD |
| **cli_tool** | Command-line tool | Intermediate | Argument parsing, user interaction |

## Running Examples

Each example includes a README with:
1. Goal description
2. OmniBuilder command to run
3. Expected outputs
4. Manual testing instructions

### General Pattern

```bash
# Navigate to example directory
cd examples/<example_name>

# Run with OmniBuilder
omnibuilder run "<goal from README>"

# Or use interactive mode
omnibuilder chat
# Then describe what you want to build
```

## Creating Custom Examples

To create your own example:

1. Create a new directory in `examples/`
2. Add a `README.md` with:
   - Clear goal description
   - OmniBuilder command
   - Expected outputs
3. Optionally add starter files or data

## Testing All Examples

```bash
# From repository root
python examples/run_all.py
```

This will:
- Run each example with OmniBuilder
- Verify outputs were created
- Run any tests
- Generate a summary report

## Tips for Using Examples

- **Start Simple**: Begin with `hello_world` to understand the basics
- **Iterate**: Use `omnibuilder chat` to refine outputs
- **Inspect**: Review generated code to learn patterns
- **Customize**: Modify goals to create variations

## Example Goals

Here are some additional goals to try:

```bash
# Web scraper
omnibuilder run "Create a web scraper for news articles with BeautifulSoup"

# Discord bot
omnibuilder run "Build a Discord bot with commands for weather and jokes"

# ETL pipeline
omnibuilder run "Create an ETL pipeline that extracts from CSV, transforms data, and loads to SQLite"

# Testing suite
omnibuilder run "Add pytest tests with 80%+ coverage to this project"

# Documentation
omnibuilder run "Generate comprehensive API documentation from this codebase"
```

## Contributing Examples

To contribute an example:

1. Fork the repository
2. Create your example in `examples/`
3. Test it thoroughly
4. Submit a pull request

Good examples:
- Have clear, specific goals
- Demonstrate real-world use cases
- Include validation/testing
- Document expected behavior
