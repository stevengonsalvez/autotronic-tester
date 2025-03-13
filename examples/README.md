# AutoGen Playwright Examples

This directory contains example scripts demonstrating various features of the AutoGen Playwright framework.

## Available Examples

### Basic Web Testing

- **run_web_test.py**: Basic example of running a web test using the framework
  - Demonstrates both group chat and direct conversation modes
  - Configurable via environment variables

### Force Mode Examples

See the [force_mode_examples](./force_mode_examples) directory for examples demonstrating the different `FORCE_MODE` settings:

- **auto_mode_example.py**: Let the LLM decide whether to use tools or generate code
- **code_generation_example.py**: Force the agent to always generate complete Python code
- **tool_usage_example.py**: Force the agent to always use tools directly

### Inheritance Example

- **inheritance_example.py**: Demonstrates the correct way to inherit from the `PlaywrightSkill` class
  - Shows proper initialization of the parent class
  - Includes error handling and retry logic
  - Provides a template for creating custom test classes

## Running the Examples

To run any of the examples:

```bash
# Make sure you have a .env file with your API keys
cp ../.env.example ../.env
# Edit the .env file with your API keys

# Run an example
python run_web_test.py

# Or run a specific force mode example
python force_mode_examples/auto_mode_example.py
```

## Common Issues and Solutions

### Inheritance Issues

When creating a class that inherits from `PlaywrightSkill`, always call the parent class's `__init__` method first:

```python
class MyTest(PlaywrightSkill):
    def __init__(self):
        super().__init__()  # Initialize the parent class first
        # Then add your own initialization code
        self.start_session("My Test Scenario")
```

Failing to call `super().__init__()` will result in errors like:
```
AttributeError: 'MyTest' object has no attribute 'report_dir'
```

### Report Directory

By default, test reports are saved to the `./reports` directory. You can customize this by passing a different path to the `PlaywrightSkill` constructor:

```python
# Custom report directory
custom_reports_dir = Path('./custom_reports')
test = CustomTest(report_dir=custom_reports_dir)
```

The directory will be automatically created if it doesn't exist.

### Browser Issues

If you encounter browser-related issues, try:
- Setting `BROWSER_HEADLESS=false` in your `.env` file to see what's happening
- Increasing the `DEFAULT_TIMEOUT` value for slow websites
- Using more robust selectors with fallbacks 