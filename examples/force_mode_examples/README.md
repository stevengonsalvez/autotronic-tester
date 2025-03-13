# Force Mode Examples

This directory contains example scripts demonstrating the different `FORCE_MODE` settings in the AutoGen Playwright framework.

## Available Examples

1. **Auto Mode** (`auto_mode_example.py`):
   - Default behavior where the LLM decides whether to use tools directly or generate code
   - Demonstrates the most flexible approach

2. **Code Generation Mode** (`code_generation_example.py`):
   - Forces the agent to always generate complete Python code
   - Useful when you need full scripts that can be saved and reused

3. **Tool Usage Mode** (`tool_usage_example.py`):
   - Forces the agent to always use tools directly
   - Best used with group chat mode for complex interactions

## Running the Examples

To run any of the examples:

```bash
# Make sure you have a .env file with your API keys
cp ../../.env.example ../../.env
# Edit the .env file with your API keys

# Run an example
python auto_mode_example.py
```

## Understanding the Output

Each example will log information about:
- The selected force mode
- How the agent is responding (generating code or using tools)
- The execution flow between agents

## When to Use Each Mode

- **Auto Mode**: When you want the LLM to decide the best approach based on the task
- **Code Generation**: When you need complete, reusable test scripts
- **Tool Usage**: When you want direct, step-by-step execution with immediate feedback

## Customizing the Examples

You can modify these examples to:
- Test different websites
- Add more complex test steps
- Experiment with different LLM providers
- Adjust timeout and retry settings

For more information, see the main README in the project root. 