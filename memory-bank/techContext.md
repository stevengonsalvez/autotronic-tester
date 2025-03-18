# Technical Context

## Technology Stack

### Core Framework
- **Python**: Primary programming language (>=3.9)
- **AutoGen**: LLM agent framework
  - v0.4 (implemented): autogen-core, autogen-agentchat, autogen-ext

### Web Testing
- **Playwright**: Step-by-step browser automation framework (>=1.41.0)
  - Using Playwright's synchronous API for browser control
- **browser-use**: Natural language browser automation library
  - Uses its own LLM agent to interpret instructions
  - Autonomous browser navigation and interaction
  - Requires langchain and langchain-openai

### LLM Integration
- **OpenAI API**: Primary LLM provider
- **Azure OpenAI API**: Alternative LLM provider
- **Anthropic API**: Support for Claude models
- **Cerebras Cloud SDK**: Alternative model support (>=0.1.0)

### Supporting Libraries
- **Python-dotenv**: Environment variable management (>=1.0.0)
- **AgentOps**: Operational metrics and logging (>=0.1.0)
- **Pandas**: Data processing for analytics (>=2.0.0)
- **Plotly**: Visualization for reports (>=5.18.0)
- **LangChain**: Framework for building LLM applications (for browser-use)

### Development Tools
- **Pytest**: Testing framework (>=7.0.0)
- **Black**: Code formatting (>=23.0.0)
- **Flake8**: Code linting (>=6.0.0)

### User Interface
- **Streamlit**: Optional web interface for test execution (>=1.31.0)

## Key Technical Concepts

### Agent Architecture in AutoGen 0.4
- **Asynchronous API**: New async/await pattern for agent communication
- **Model Clients**: Direct model client configuration instead of llm_config
- **Message Types**: Structured message types like TextMessage
- **Team Structure**: RoundRobinGroupChat or SelectorGroupChat for agent coordination
- **Tools Integration**: Direct tool registration with assistant agents

### Browser Automation Approaches

#### Playwright Approach
- **Explicit Actions**: Step-by-step control of browser actions
- **Precise Control**: Fine-grained control over browser behavior
- **Selector-Based**: Uses CSS selectors and XPath for element targeting
- **Synchronous API**: Uses a synchronous API for browser interaction
- **Tool Integration**: Integrated as tools for AutoGen agents

#### Browser-use Approach
- **Natural Language**: Takes natural language instructions directly
- **Agent-Based**: Uses its own LLM agent to interpret and execute tasks
- **Autonomous**: Makes its own decisions about how to complete tasks
- **Visual Understanding**: Can identify elements based on appearance
- **Asynchronous API**: Uses async/await pattern for execution

### Environment Configuration
- **.env**: Environment variables for configuration
- **Configuration Parameters**: Model selection, API keys, execution settings
- **Chrome Path**: Optional configuration for browser-use

## Technical Constraints

1. **API Limitations**:
   - LLM API rate limits and token limits
   - Browser automation limitations in complex UI scenarios
   - Different capabilities between Playwright and browser-use
   - Additional token usage with browser-use's agent

2. **Performance Considerations**:
   - Test execution speed limited by browser interactions
   - LLM inference time impacts execution speed
   - Multiple LLM calls with browser-use increases execution time
   - Autonomous navigation may be less efficient for known paths

3. **Security Constraints**:
   - API keys and credentials management
   - Secure execution of dynamically generated code
   - Local browser security considerations
   - LLM token exposure with browser-use instructions

4. **Compatibility Requirements**:
   - Browser version compatibility
   - LLM API version compatibility
   - Python dependency management for optional packages
   - LangChain compatibility for browser-use

## Technical Workflows

### Playwright Test Execution Workflow
1. Load environment configuration
2. Initialize agents and tools
3. Parse natural language test instructions
4. Convert to executable test steps
5. Execute steps against target website using PlaywrightSkill
6. Capture and analyze results
7. Generate test report

### Browser-use Test Execution Workflow
1. Load environment configuration
2. Initialize browser-use agent
3. Provide natural language test instructions directly
4. Agent autonomously navigates and interacts with website
5. Capture results and screenshots
6. Complete task and report results

### Multi-Approach Handling
1. Determine appropriate browser automation approach
2. Initialize the corresponding skill
3. Execute test using the selected approach
4. Handle approach-specific outputs and errors
5. Generate appropriate reports

### Error Handling Workflow
1. Detect error during test execution
2. Capture error details and screenshots
3. For Playwright: Route to debug agent for analysis
4. For browser-use: Let the agent attempt recovery or report failure
5. Continue or terminate test execution based on severity

### Reporting Workflow
1. Capture execution details
2. Store screenshots at key points
3. Compile execution logs and metrics
4. Generate comprehensive test report
