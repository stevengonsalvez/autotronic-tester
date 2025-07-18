# Technical Context

## Technology Stack

### Core Framework
- **Python**: Primary programming language (>=3.9)
- **AutoGen**: LLM agent framework
  - v0.2 (current): ag2 >=0.2.0
  - v0.4 (target): autogen-core, autogen-agentchat, autogen-ext

### Web Testing
- **Playwright**: Browser automation framework (>=1.41.0)
- **Sync API**: Using Playwright's synchronous API for browser control

### LLM Integration
- **OpenAI API**: Primary LLM provider
- **Azure OpenAI API**: Alternative LLM provider
- **Cerebras Cloud SDK**: Alternative model support (>=0.1.0)

### Supporting Libraries
- **Python-dotenv**: Environment variable management (>=1.0.0)
- **AgentOps**: Operational metrics and logging (>=0.1.0)
- **Pandas**: Data processing for analytics (>=2.0.0)

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

### Playwright Integration
- **Sync API**: Using the synchronous API for browser control
- **Action Methods**: Navigation, clicking, form filling, etc.
- **Error Handling**: Robust error handling for browser interactions
- **Screenshot Capture**: Automatic screenshot capture for test evidence

### Environment Configuration
- **.env**: Environment variables for configuration
- **Configuration Parameters**: Model selection, API keys, execution settings

## Technical Constraints

1. **API Limitations**:
   - LLM API rate limits and token limits
   - Browser automation limitations in complex UI scenarios

2. **Performance Considerations**:
   - Test execution speed limited by browser interactions
   - LLM inference time can impact test execution speed

3. **Security Constraints**:
   - API keys and credentials management
   - Secure execution of dynamically generated code

4. **Compatibility Requirements**:
   - Browser version compatibility
   - LLM API version compatibility

## Technical Workflows

### Test Execution Workflow
1. Load environment configuration
2. Initialize agents and teams
3. Parse natural language test instructions
4. Convert to executable test steps
5. Execute steps against target website
6. Capture and analyze results
7. Generate test report

### Error Handling Workflow
1. Detect error during test execution
2. Capture error details and screenshots
3. Route to debug agent for analysis
4. Attempt recovery or provide detailed failure information
5. Continue or terminate test execution based on severity

### Reporting Workflow
1. Capture step-by-step execution details
2. Store screenshots at key points
3. Compile execution logs and metrics
4. Generate comprehensive test report
