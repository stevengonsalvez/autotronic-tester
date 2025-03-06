# System Patterns

## Architecture Overview

The Autogen-Tester project follows a multi-agent architecture where different agents collaborate to execute web testing tasks. The system is designed around these core principles:

1. **Agent Specialization**: Different agents handle specific aspects of the testing process
2. **Orchestrated Collaboration**: A coordinated interaction pattern between agents
3. **Skill Encapsulation**: Browser automation capabilities are encapsulated in a dedicated skill module
4. **Event-Driven Communication**: In AutoGen 0.4, agents communicate through async events

## Key Architectural Components

### 1. Agent Types and Roles

The system uses several specialized agents:

- **Web Testing Agent**: The primary agent responsible for understanding test instructions and planning test steps
- **Debug Agent**: Specialized in troubleshooting test execution failures
- **Security Admin Agent**: Reviews and approves browser automation code before execution
- **Executor Agent**: In the old architecture, this executed the Playwright commands (being refactored)

In the new AutoGen 0.4 architecture, these are being consolidated where appropriate, as tool execution can now be handled directly by assistant agents.

### 2. Team Organization Pattern

The system uses a team pattern where agents collaborate in a controlled conversation flow:

- In AutoGen 0.2: Used `GroupChat` with custom speaker selection
- In AutoGen 0.4: Using `SelectorGroupChat` or `RoundRobinGroupChat` with appropriate termination conditions

### 3. Message Flow Pattern

Messages flow between agents in a specific pattern:

1. Web Testing Agent interprets the test instruction and plans steps
2. Security Admin reviews and approves/rejects the steps
3. Steps are executed and results returned
4. Debug Agent intervenes if failures occur
5. Process continues until test completion or maximum iterations

### 4. Skill Integration Pattern

The PlaywrightSkill module integrates with the agents through:

- A clear interface for browser automation actions
- Comprehensive error handling and reporting
- Screenshot capture for test evidence
- Session management for browser instances

### 5. Tool Integration Pattern

In AutoGen 0.4, tools are integrated directly with agents:

- Assistant Agents can execute tools without needing a separate UserProxy
- Tools like PlaywrightSkill can be registered directly with agents
- Tool execution results flow back into the conversation

## Design Patterns

1. **Agent Responsibility Pattern**:
   - Each agent has a clear, single responsibility
   - Agents interact through well-defined interfaces

2. **Conversation Control Pattern**:
   - Custom speaker selection controls the flow of conversation
   - Termination conditions define when conversations end

3. **Error Recovery Pattern**:
   - Debug agent intervenes when errors occur
   - Retry mechanisms handle transient failures

4. **Reporting Pattern**:
   - Comprehensive test reports are generated
   - Screenshots provide visual evidence
   - Step-by-step recording of actions and results

## Data Flow

1. Test instructions enter the system as natural language
2. Instructions are parsed and converted into executable test steps
3. Steps are executed against the target web application
4. Results are captured, analyzed, and reported
5. Failures trigger debugging and recovery mechanisms
