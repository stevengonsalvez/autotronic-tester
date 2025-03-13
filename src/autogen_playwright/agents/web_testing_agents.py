import logging
import os
import re
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union, Sequence

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.messages import ChatMessage, TextMessage, AgentEvent
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

from ..llm.provider import LLMProvider
from ..prompts import WEB_TESTER_PROMPT, DEBUG_AGENT_PROMPT, SECURITY_ADMIN_PROMPT, CODE_EXECUTOR_PROMPT
from ..skills.playwright_skill import PlaywrightSkill

logger = logging.getLogger(__name__)

# Tool functions for playwright operations
def start_browser_session(scenario_name: str = "Web Test") -> str:
    """
    Start a new browser session.
    
    Args:
        scenario_name: Name of the test scenario
        
    Returns:
        String result of the operation
    """
    try:
        skill = PlaywrightSkill()
        result = skill.start_session(scenario_name)
        return f"Browser session started for scenario: {scenario_name}"
    except Exception as e:
        return f"Error starting browser session: {str(e)}"

def navigate_to_url(url: str, wait_for_load: bool = True) -> str:
    """
    Navigate to a URL.
    
    Args:
        url: The URL to navigate to
        wait_for_load: Whether to wait for the page to fully load
        
    Returns:
        String result of the operation
    """
    try:
        skill = PlaywrightSkill()
        skill.navigate(url, wait_for_load)
        return f"Navigated to URL: {url}"
    except Exception as e:
        return f"Error navigating to {url}: {str(e)}"

def click_element(selector: str) -> str:
    """
    Click an element on the page.
    
    Args:
        selector: CSS selector for the element to click
        
    Returns:
        String result of the operation
    """
    try:
        skill = PlaywrightSkill()
        skill.click_element(selector)
        return f"Clicked element with selector: {selector}"
    except Exception as e:
        return f"Error clicking element {selector}: {str(e)}"

def fill_form_field(selector: str, value: str) -> str:
    """
    Fill a form field.
    
    Args:
        selector: CSS selector for the form field
        value: Value to enter in the field
        
    Returns:
        String result of the operation
    """
    try:
        skill = PlaywrightSkill()
        skill.fill_form(selector, value)
        return f"Filled form field {selector} with value: {value}"
    except Exception as e:
        return f"Error filling form field {selector}: {str(e)}"

def verify_element(selector: str) -> str:
    """
    Verify an element exists on the page.
    
    Args:
        selector: CSS selector for the element to verify
        
    Returns:
        String result of the operation
    """
    try:
        skill = PlaywrightSkill()
        result = skill.verify_element_exists(selector)
        return f"Element {selector} exists: {result}"
    except Exception as e:
        return f"Error verifying element {selector}: {str(e)}"

def verify_text(text: str) -> str:
    """
    Verify text exists on the page.
    
    Args:
        text: Text to verify on the page
        
    Returns:
        String result of the operation
    """
    try:
        skill = PlaywrightSkill()
        result = skill.verify_text_content(text)
        return f"Text '{text}' exists on page: {result}"
    except Exception as e:
        return f"Error verifying text '{text}': {str(e)}"

def hover_over_element(selector: str) -> str:
    """
    Hover over an element on the page.
    
    Args:
        selector: CSS selector for the element to hover over
        
    Returns:
        String result of the operation
    """
    try:
        skill = PlaywrightSkill()
        result = skill.hover_element(selector)
        return f"Hover over element {selector}: {'Successful' if result else 'Failed'}"
    except Exception as e:
        return f"Error hovering over element {selector}: {str(e)}"

def take_page_screenshot(name: str = "screenshot", full_page: bool = False) -> str:
    """
    Take a screenshot of the page.
    
    Args:
        name: Name for the screenshot file (without extension)
        full_page: Whether to capture the full page or just the viewport
        
    Returns:
        String result of the operation
    """
    try:
        skill = PlaywrightSkill()
        skill.take_screenshot(name, full_page)
        return f"Screenshot taken: {name}"
    except Exception as e:
        return f"Error taking screenshot {name}: {str(e)}"

def end_browser_session(status: str = "Completed") -> str:
    """
    End the browser session.
    
    Args:
        status: Final status of the test
        
    Returns:
        String result of the operation
    """
    try:
        skill = PlaywrightSkill()
        skill.end_session(status)
        return f"Browser session ended with status: {status}"
    except Exception as e:
        return f"Error ending browser session: {str(e)}"
    
    except Exception as e:
        logger.error(f"Error executing Playwright operation: {str(e)}")
        return f"Error executing {operation}: {str(e)}"


def selector_func(messages: Sequence[AgentEvent | ChatMessage]) -> Optional[str]:
    """
    Custom selector function for the SelectorGroupChat to determine the next speaker.
    
    Args:
        messages: The message history
        
    Returns:
        The name of the next agent to speak, or None to use LLM-based selection
    """
    # Check if we're in forced code generation mode
    force_mode = os.getenv('FORCE_MODE', 'auto').lower()
    
    if not messages:
        # Start with web_tester if no messages
        return "web_tester"
    
    last_message = messages[-1]
    last_speaker = last_message.source
    
    # Extract content from the last message
    if isinstance(last_message, TextMessage):
        content = last_message.content.lower()
    else:
        # For other message types, we can't easily check content
        # Default to letting the LLM choose
        return None
    
    # In code generation mode, we want to always route web_tester to security_admin
    if force_mode == 'code_generation' and last_speaker == "web_tester":
        logger.info("In code generation mode, routing to security_admin for code review")
        return "security_admin"
    
    # Check for execution errors or failures
    error_patterns = [
        r"failed to .+: timeout \d+ms exceeded",
        r"error: .+",
        r"failed to .+: both normal and force click failed",
        r"element is not visible",
        r"element .+ not found",
        r"navigation timeout",
        r"execution failed"
    ]
    
    has_error = any(re.search(pattern, content) for pattern in error_patterns)
    
    if has_error and last_speaker == "code_executor":
        # If executor reports an error, route to debug_agent
        logger.info("Routing to debug_agent due to execution error")
        return "debug_agent"
        
    if last_speaker == "debug_agent":
        # After debug_agent provides suggestions, route back to web_tester
        logger.info("Routing back to web_tester to implement fixes")
        return "web_tester"
        
    if last_speaker == "web_tester":
        # Route web_tester's actions to security_admin for approval
        logger.info("Routing to security_admin for code review")
        return "security_admin"
        
    if last_speaker == "security_admin":
        if "approved" in content:
            # If admin approves, route to executor
            logger.info("Code approved by admin, routing to executor")
            return "code_executor"
        else:
            # If admin rejects, route back to web_tester for modifications
            logger.info("Code rejected by admin, routing back to web_tester")
            return "web_tester"
    
    # Let LLM decide for other cases
    return None


async def create_web_testing_agents(use_group_chat: bool = True, model_client: Optional[ChatCompletionClient] = None) -> Union[
    Tuple[AssistantAgent, AssistantAgent, AssistantAgent, CodeExecutorAgent, SelectorGroupChat], 
    Tuple[AssistantAgent, CodeExecutorAgent]
]:
    """
    Create and initialize web testing agents
    
    Args:
        use_group_chat: Whether to use SelectorGroupChat for better conversation control (default: True)
        model_client: Optional custom model client to use (default: None, will create a new one)
        
    Returns:
        If use_group_chat=True:
            Tuple[AssistantAgent, AssistantAgent, AssistantAgent, CodeExecutorAgent, SelectorGroupChat]
        If use_group_chat=False:
            Tuple[AssistantAgent, CodeExecutorAgent]
    """
    # Get model client if not provided
    if model_client is None:
        model_client = LLMProvider().get_model_client()
    logger.info(f"LOG: Creating agents with model client")
    
    # Check if we should force code generation or tool usage
    force_mode = os.getenv('FORCE_MODE', 'auto').lower()
    logger.info(f"LOG: Using force_mode: {force_mode}")
    
    # Determine which prompt to use based on force_mode
    if force_mode == 'code_generation':
        # Use a prompt that instructs the agent to always generate code
        web_tester_prompt = WEB_TESTER_PROMPT + "\n\nIMPORTANT: ALWAYS generate complete Python code for all tasks. DO NOT use direct tool calls."
        use_tools = False
    elif force_mode == 'tool_usage':
        # Use a prompt that instructs the agent to always use tools
        web_tester_prompt = WEB_TESTER_PROMPT + "\n\nIMPORTANT: ALWAYS use the provided tools directly. DO NOT generate complete Python code."
        use_tools = True
    else:
        # Default auto mode - let the LLM decide
        web_tester_prompt = WEB_TESTER_PROMPT
        use_tools = True
    
    # Create the testing agent
    web_tester = AssistantAgent(
        name="web_tester",
        system_message=web_tester_prompt,
        model_client=model_client,
        tools=[
            start_browser_session,
            navigate_to_url,
            click_element,
            fill_form_field,
            verify_element,
            verify_text,
            hover_over_element,
            take_page_screenshot,
            end_browser_session
        ] if use_tools else [],
        description="A web testing agent that plans and executes web test scenarios."
    )

    # Create the debugging agent
    debug_agent = AssistantAgent(
        name="debug_agent",
        system_message=DEBUG_AGENT_PROMPT,
        model_client=model_client,
        description="A debugging agent that helps resolve issues during test execution."
    )

    # Create the security admin agent
    security_admin = AssistantAgent(
        name="security_admin",
        system_message=SECURITY_ADMIN_PROMPT,
        model_client=model_client,
        description="A security admin agent that reviews and approves browser automation code."
    )

    # Create the code executor agent
    # Create working directory if it doesn't exist
    work_dir = Path("workspace")
    work_dir.mkdir(exist_ok=True)
    
    code_executor = CodeExecutorAgent(
        name="code_executor",
        code_executor=LocalCommandLineCodeExecutor(
            work_dir=work_dir,
            timeout=int(os.getenv('EXECUTION_TIMEOUT', '300'))  # 5 minutes default timeout
        ),
        description="An executor agent that runs Python code for test automation."
    )
    
    # Tools are already registered during agent creation
    
    if use_group_chat:
        # Create termination conditions
        text_termination = TextMentionTermination("you can find the full test report at:")
        max_message_termination = MaxMessageTermination(30)  # Terminate after 30 messages
        termination = text_termination | max_message_termination
        
        # Create the group chat
        group_chat = SelectorGroupChat(
            participants=[web_tester, debug_agent, security_admin, code_executor],
            model_client=model_client,  # Use same model for selection
            termination_condition=termination,
            selector_func=selector_func,
            max_turns=15,
        )
        
        # Return all components
        return (
            web_tester,
            debug_agent,
            security_admin,
            code_executor,
            group_chat
        )
    
    # For simpler mode, just return the main agent and executor
    return web_tester, code_executor

# Export only the function
__all__ = ['create_web_testing_agents']