# AutoGen Playwright

An experimental framework exploring automated web testing using Microsoft's AutoGen multi-agent framework (v0.4) combined with Playwright. This project aims to investigate the potential of LLM-powered agents in automated testing scenarios.

## Overview
This project explores the intersection of Large Language Models (LLMs) and automated testing by leveraging AutoGen's multi-agent architecture. The goal is to create more intelligent and adaptable automated tests that can understand test requirements in natural language and translate them into executable test scenarios.

## Features
- **LLM-Powered Test Generation**: Converts natural language test requirements into executable Playwright test scripts
- **Multi-Agent Testing Architecture**:
  - Test Planning Agent: Analyzes requirements and creates test strategies
  - Test Execution Agent: Implements and runs Playwright tests
  - User Proxy Agent: Handles human-in-the-loop interactions when needed
- **Playwright Integration**: 
  - Full browser automation support
  - Cross-browser testing capabilities
  - Network interception and mocking
- **Advanced Reporting**:
  - Detailed test execution logs
  - Automatic screenshot capture on failures
  - Markdown report generation with visual evidence
  - AgentOps integration for monitoring agent interactions
- **Flexible Configuration**:
  - Customizable LLM providers
  - Configurable browser settings
  - Environment-based configuration
- **Execution Mode Control**:
  - Control whether agents use tools directly or generate code
  - Switch between modes using environment variables

## Installation
```bash
pip install -e .
```

## Prerequisites
- Python 3.9 or higher
- OpenAI API key or other supported LLM provider
- AgentOps API key (optional, for monitoring)

## AutoGen Version
This project uses AutoGen 0.4, which introduces a new API with several improvements:
- Asynchronous execution model for better performance
- Enhanced team collaboration capabilities
- Direct tool integration with assistant agents
- Improved observability and control

## Quick Start
```python
import asyncio
from autogen_core import CancellationToken
from autogen_agentchat.ui import Console
from autogen_playwright import create_web_testing_agents

async def run_test():
    # Create web testing agents
    agents = await create_web_testing_agents(use_group_chat=True)
    web_tester, debug_agent, security_admin, code_executor, group_chat = agents
    
    # Define test scenario
    test_message = """
    Test Scenario: Verify user login flow
    1. Navigate to login page
    2. Enter valid credentials
    3. Verify successful login
    """
    
    # Run the test
    stream = group_chat.run_stream(task=test_message, 
                                   cancellation_token=CancellationToken())
    
    # Display the results in real-time
    await Console(stream)

# Run the test
asyncio.run(run_test())
```

## Configuration
Create a `.env` file in your project root:
```
# LLM Configuration
OPENAI_API_KEY=your_api_key
MODEL_NAME=gpt-4

# Playwright Settings
BROWSER_TYPE=chromium
HEADLESS=true

# Agent Behavior
USE_GROUP_CHAT=true
FORCE_MODE=auto  # Options: auto, code_generation, tool_usage

# Monitoring
AGENTOPS_API_KEY=your_api_key
```

### Execution Mode Control
The framework provides control over how agents execute tasks through the `FORCE_MODE` environment variable:

- **auto** (default): Let the LLM decide whether to use tools directly or generate code
- **code_generation**: Force the agent to always generate complete Python code
- **tool_usage**: Force the agent to always use tools directly

This gives you flexibility in how tests are executed:
```python
# Force code generation mode
os.environ['FORCE_MODE'] = 'code_generation'

# Force tool usage mode
os.environ['FORCE_MODE'] = 'tool_usage'

# Let the LLM decide (default)
os.environ['FORCE_MODE'] = 'auto'
```

## LLM Caching
The framework implements disk-based caching for LLM responses to optimize costs and improve response times:

### Cache Configuration
- **Enable/Disable**: Set via `LLM_CACHE_ENABLE` (defaults to true)
- **Cache Location**: Configured through `LLM_CACHE_PATH` (defaults to '/tmp/autogen-playwright-cache')
- **Cache Seeding**: Optional cache seed via `LLM_CACHE_SEED` for reproducible results

### What Gets Cached
- All LLM interactions including:
  - Test planning conversations
  - Test step generation
  - Response analysis
  - Error handling decisions

### Cache Behavior
- **Cache Keys**: Generated based on the conversation context and prompt
- **Hit/Miss Logging**: All cache interactions are logged for monitoring
- **Persistence**: Cache files are stored on disk and persist between runs
- **Cost Savings**: Repeated test scenarios reuse cached responses

### Monitoring Cache Performance
The framework includes built-in observability features leveraging AutoGen 0.4's event-driven architecture:

```python
from autogen_core import CancellationToken
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.cache import ChatCompletionCache
from autogen_ext.cache_store.diskcache import DiskCacheStore
from diskcache import Cache
import tempfile

# Initialize the model client with caching
with tempfile.TemporaryDirectory() as cache_dir:
    # Create base model client
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o",
        api_key="your-api-key"
    )
    
    # Add caching
    cache_store = DiskCacheStore(Cache(cache_dir))
    cached_client = ChatCompletionCache(model_client, cache_store)
    
    # Create agent with cached client
    agent = AssistantAgent(
        name="web_tester",
        system_message="You are a web testing agent.",
        model_client=cached_client
    )
    
    # Use in-memory or streaming to monitor performance
    response = await agent.on_messages_stream(
        [{"content": "Test this website", "source": "user"}],
        CancellationToken()
    )
```

## Project Goals
1. **Explore AutoGen Capabilities**: Investigate how AutoGen's multi-agent system can be applied to web testing
2. **Natural Language Testing**: Enable test creation and maintenance using natural language
3. **Intelligent Test Maintenance**: Leverage LLMs for test adaptation and self-healing
4. **Best Practices Integration**: Combine AI capabilities with established testing practices

## Current Limitations & Areas of Exploration
- LLM context handling for complex test scenarios
- Test stability and reproducibility
- Cost-effectiveness of LLM-based testing
- Integration with existing test frameworks
- Performance optimization

## Contributing
This is an experimental project and contributions are welcome. Please feel free to submit issues and pull requests.

## License
MIT License 