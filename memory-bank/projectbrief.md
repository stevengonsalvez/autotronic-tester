# Project Brief: Autogen-Tester

## Project Summary
Autogen-Tester is a Python framework that integrates Microsoft's AutoGen with the Playwright browser automation tool to create AI-driven web testing agents. The project aims to enable automated testing of web applications through natural language instructions, leveraging LLM capabilities to understand and execute web testing scenarios.

## Core Requirements

1. **Refactor from AutoGen 0.2 to 0.4**:
   - Adapt the codebase to use the new AutoGen 0.4 API patterns
   - Preserve all existing functionality while leveraging new features
   - Maintain compatibility with Playwright for web testing

2. **Maintain Core Testing Capabilities**:
   - Execute web test scenarios described in natural language
   - Perform common browser interactions (navigation, clicking, form filling)
   - Handle test failures and debugging gracefully
   - Generate comprehensive test reports

3. **Preserve Architecture Pattern**:
   - Keep the agent-based architecture with specialized roles
   - Adapt to new agent patterns in AutoGen 0.4
   - Maintain separation between test logic and browser automation

## Technical Requirements

1. **Dependencies**:
   - Replace ag2 with autogen-core, autogen-agentchat, and autogen-ext
   - Maintain compatibility with Playwright >=1.41.0

2. **Agent Implementation**:
   - Update to use the async API pattern of AutoGen 0.4
   - Replace old agent types with new equivalents
   - Implement proper message handling and conversation flow

3. **Error Handling**:
   - Ensure robust error handling during test execution
   - Provide clear error reports and debugging information
   - Implement proper recovery mechanisms

4. **Reporting**:
   - Maintain comprehensive test reporting
   - Include screenshots, logs, and detailed test steps

## Success Criteria

1. All existing test scenarios can be executed with the refactored code
2. Test reports are generated with the same level of detail as before
3. Code follows the best practices of AutoGen 0.4
4. Performance is maintained or improved
5. Documentation is updated to reflect the new implementation
