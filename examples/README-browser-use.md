# Browser-Use Example

This example demonstrates how to use the browser-use integration with the AutoGen Playwright framework.

## Prerequisites

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your environment variables:
   ```
   # Create a .env file in the project root
   cp ../.env.example ../.env
   
   # Edit the .env file with your API keys
   # Required:
   # - LLM_PROVIDER (openai, anthropic, azure)
   # - LLM_API_KEY (your API key)
   # - LLM_MODEL (gpt-4o, claude-3-opus-20240229, etc.)
   ```

3. Make sure you have Chrome installed on your system.

## Running the Example

Run the EE website test example:
```bash
python browser_use_example.py
```

Run the custom test example:
```bash
python browser_use_example.py --custom
```

## How It Works

The browser-use example uses the BrowserUseSkill to:

1. Initialize a Chrome browser using browser-use
2. Create an agent with the LLM specified in your .env file
3. Execute a series of test steps as a single natural language task
4. Capture screenshots during execution
5. Report the results

The agent autonomously interprets and executes the instructions without requiring step-by-step code.

## Customizing

You can customize the example by:

1. Changing the test steps in the script
2. Specifying a custom Chrome path
3. Setting headless mode (BROWSER_HEADLESS=true in .env)
4. Using different LLM providers (change LLM_PROVIDER and LLM_MODEL in .env)

## Troubleshooting

If you encounter issues:

1. Make sure Chrome is installed and accessible
2. Check that your API keys are correct
3. Verify that you have the required dependencies installed
4. Look at the logs for detailed error messages

## More Information

See the [browser-use integration documentation](../docs/browser_use_integration.md) for more details on using browser-use with this framework.
