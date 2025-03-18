# Browser Use Integration

This document explains how to use the browser-use integration with the AutoGen Playwright framework.

## Overview

Browser-use is an alternative browser automation solution that uses an LLM agent to directly interpret and execute natural language instructions. Unlike Playwright, which requires specific code for each browser action, browser-use can understand high-level instructions and determine the appropriate actions automatically.

## Installation

To use the browser-use integration, install the required packages:

```bash
pip install browser-use langchain-openai
```

These are already included in the requirements.txt file.

## LLM Model Configuration

The browser-use integration uses the same LLM configuration as the rest of the framework. It supports:

- **OpenAI**: GPT-4, GPT-4o, and other OpenAI models
- **Anthropic**: Claude models (via LangChain Anthropic integration)
- **Azure OpenAI**: Azure-hosted OpenAI models
- **Local models**: Supported via LangChain integrations

The configuration is read from the same environment variables:

```
# LLM Configuration
# Available providers: openai, anthropic, azure
LLM_PROVIDER=openai

# API Keys
LLM_API_KEY=your-api-key-here

# Model name
LLM_MODEL=gpt-4o

# Optional Configuration
LLM_TEMPERATURE=0.7
LLM_REQUEST_TIMEOUT=600
```

## Basic Usage

### Standalone Example

You can use the browser-use integration directly:

```python
import asyncio
from src.autogen_playwright.skills.browser_use_skill import BrowserUseSkill

async def main():
    # Create BrowserUseSkill instance
    skill = BrowserUseSkill()
    
    # Set up the browser and agent
    await skill.setup()
    
    # Define a task in natural language
    task = """
    Execute the following test steps:
    1. Navigate to google.com
    2. Search for "browser-use github"
    3. Click on the first result
    4. Take a screenshot of the page
    """
    
    # Execute the task
    result = await skill.execute_task(task)
    print(f"Task result: {result}")
    
    # Clean up
    await skill.cleanup()

# Run the example
asyncio.run(main())
```

### Chrome Path Specification

If you need to specify the path to your Chrome executable:

```python
# For macOS
skill = BrowserUseSkill(chrome_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')

# For Windows
skill = BrowserUseSkill(chrome_path='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe')

# For Linux
skill = BrowserUseSkill(chrome_path='/usr/bin/google-chrome')
```

### Running in Headless Mode

To run the browser in headless mode (no visible browser window):

```python
skill = BrowserUseSkill(headless=True)
```

You can also set this via environment variable:

```
BROWSER_HEADLESS=true
```

## Example Script

An example script is available at `examples/browser_use_example.py` which demonstrates the browser-use integration. You can run it with:

```bash
python examples/browser_use_example.py
```

To run a custom example:

```bash
python examples/browser_use_example.py --custom
```

## Key Differences from Playwright

Browser-use offers a different approach to browser automation:

1. **Natural Language Instructions**: Browser-use accepts natural language instructions directly instead of requiring specific API calls.

2. **LLM-Powered Navigation**: Browser-use uses its own LLM agent to determine how to interact with the web page.

3. **Autonomous Operation**: Once given a task, browser-use operates autonomously to complete it without needing step-by-step instructions.

4. **Visual Understanding**: Browser-use can understand and interact with elements based on their visual appearance.

## Example Tasks

Browser-use works best with higher-level task descriptions:

```python
# Good task description
task = """
Navigate to twitter.com and search for the latest posts about "artificial intelligence".
Take screenshots of the first 3 results and summarize them.
"""

# Another good task description
task = """
Visit amazon.com, search for "wireless headphones", and filter for products
with 4 stars or higher. Collect the names and prices of the top 5 results.
"""
```

## Task Structure

When working with a series of test steps, it's best to structure them clearly:

```python
test_steps = [
    "Navigate to ee.co.uk",
    "Accept cookies in the OneTrust banner",
    "Hover over 'Broadband' in the global navigation menu",
    "Click to 'explore broadband' within the submenu",
    "Analyze and summarize the page content"
]

# Format steps as a single task
task = "\n".join([f"{i+1}. {step}" for i, step in enumerate(test_steps)])
task = f"Execute the following test steps:\n{task}\n\nTake screenshots for evidence."
```

## Benefits and Limitations

### Benefits
- Simpler to use for complex tasks
- Requires less code
- Can handle dynamic websites better
- More human-like browsing behavior

### Limitations
- Less precise control over individual actions
- May be slower for simple, well-defined tasks
- Uses more tokens due to LLM agent interaction
- Less debuggable when issues occur

## Technical Details

### LangChain Integration

The BrowserUseSkill uses our custom LangChainProvider which leverages the same environment configuration as the rest of the framework. This ensures consistent LLM usage across both AutoGen and browser-use components.

The provider automatically:

1. Reads the LLM configuration from environment variables
2. Creates the appropriate LangChain LLM instance
3. Passes it to the browser-use Agent

This integration allows you to switch LLM providers without changing your code, just by updating environment variables.
