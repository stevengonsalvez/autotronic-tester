# Observability in AutoGen Playwright

This document explains how to use the observability features in AutoGen Playwright to monitor and analyze your test executions.

## Overview

AutoGen 0.4 introduces a powerful event-driven architecture that allows for comprehensive observability. The AutoGen Playwright framework leverages this to provide:

1. **Event Logging**: Capture all events during test execution
2. **Token Usage Tracking**: Monitor LLM token consumption and costs
3. **Session Statistics**: Get detailed statistics about test sessions
4. **HTML Reports**: Generate interactive visualizations and reports

## Getting Started

### 1. Setting Up Event Logging

To enable event logging, you need to create and register an event listener:

```python
from autogen_core.events import register_listener
from autogen_playwright.ops.event_logger import SQLiteEventLogger

# Create the event logger
db_path = Path("./runtime_logs/autogen_logs.db")
event_logger = SQLiteEventLogger(db_path=db_path)

# Register the event listener with AutoGen
register_listener(event_logger)
```

### 2. Accessing Session Statistics

After test execution, you can get statistics about token usage and costs:

```python
# Print session statistics
event_logger.print_session_summary(session_id)
```

This will output information like:

```
==================================================
SESSION SUMMARY: session_12345
==================================================
Total Requests:      15
Prompt Tokens:       5432
Completion Tokens:   2345
Total Tokens:        7777
--------------------------------------------------
Prompt Cost:         $0.1629
Completion Cost:     $0.1407
Total Cost:          $0.3036
==================================================
```

### 3. Generating HTML Reports

For more detailed analysis, you can generate interactive HTML reports:

```python
from autogen_playwright.ops.report_generator import ReportGenerator

# Generate HTML report
report_generator = ReportGenerator(db_path=db_path)
report_path = Path("./reports/autogen_report.html")
report_generator.generate_html_report(report_path, session_id)
```

The HTML report includes:
- Token usage statistics
- Cost analysis
- Token usage over time chart
- Agent activity visualization

## Event Types

The event logger captures various event types from AutoGen:

- **LLMCall**: LLM API calls with token usage
- **MessageReceived**: Messages received by agents
- **MessageSent**: Messages sent by agents
- **AgentAction**: Actions taken by agents
- **ToolCall**: Tool invocations

## Database Schema

The event logger stores data in a SQLite database with the following tables:

### events

Stores all events with their metadata:

| Column | Description |
|--------|-------------|
| id | Unique identifier |
| timestamp | Event timestamp |
| event_type | Type of event |
| session_id | Session identifier |
| agent_id | Agent identifier |
| payload | JSON payload of the event |

### llm_calls

Stores LLM API call details:

| Column | Description |
|--------|-------------|
| id | Unique identifier |
| timestamp | Call timestamp |
| session_id | Session identifier |
| agent_id | Agent identifier |
| model | LLM model used |
| prompt_tokens | Number of prompt tokens |
| completion_tokens | Number of completion tokens |
| total_tokens | Total tokens used |
| request | Request payload |
| response | Response payload |

## Example Usage

See the [observability_example.py](../examples/observability_example.py) for a complete example of how to use these features.

## Best Practices

1. **Always register the event listener early** in your application, before creating any agents
2. **Use session IDs** to track and analyze specific test runs
3. **Generate reports after test completion** for comprehensive analysis
4. **Monitor token usage and costs** to optimize your tests

## Extending Observability

You can extend the observability features by:

1. Creating custom event listeners
2. Adding new visualizations to the report generator
3. Implementing real-time monitoring dashboards
4. Integrating with external monitoring systems 