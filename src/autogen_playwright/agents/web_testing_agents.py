import logging
import os
import re
from typing import Optional, List, Dict, Any, Tuple, Union, Sequence

from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.messages import ChatMessage, TextMessage, AgentEvent
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_core import CancellationToken
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

from ..llm.provider import LLMProvider
from ..prompts import WEB_TESTER_PROMPT, DEBUG_AGENT_PROMPT, SECURITY_ADMIN_PROMPT
from ..skills.playwright_skill import PlaywrightSkill

logger = logging.getLogger(__name__)

# Tool function to execute playwright operations
def execute_playwright_operation(operation: str, **kwargs) -> str:
    """
    Execute a Playwright operation.
    
    Args:
        operation: The name of the operation to execute
        **kwargs: Arguments for the operation
        
    Returns:
        String result of the operation
    """
    try:
        # Initialize PlaywrightSkill if not already initialized
        skill = PlaywrightSkill()
        
        # Map operation to method
        if operation == "start_session":
            scenario_name = kwargs.get("scenario_name", "Web Test")
            result = skill.start_session(scenario_name)
            return f"Browser session started for scenario: {scenario_name}"
            
        elif operation == "navigate":
            url = kwargs.get("url")
            wait_for_load = kwargs.get("wait_for_load", True)
            skill.navigate(url, wait_for_load)
            return f"Navigated to URL: {url}"
            
        elif operation == "click_element":
            selector = kwargs.get("selector")
            skill.click_element(selector)
            return f"Clicked element with selector: {selector}"
            
        elif operation == "fill_form":
            selector = kwargs.get("selector")
            value = kwargs.get("value")
            skill.fill_form(selector, value)
            return f"Filled form field {selector} with value: {value}"
            
        elif operation == "verify_element_exists":
            selector = kwargs.get("selector")
            result = skill.verify_element_exists(selector)
            return f"Element {selector} exists: {result}"
            
        elif operation == "verify_text_content":
            text = kwargs.get("text")
            result = skill.verify_text_content(text)
            return f"Text '{text}' exists on page: {result}"
            
        elif operation == "hover_element":
            selector = kwargs.get("selector")
            result = skill.hover_element(selector)
            return f"Hover over element {selector}: {'Successful' if result else 'Failed'}"
            
        elif operation == "take_screenshot":
            name = kwargs.get("name", "screenshot")
            full_page = kwargs.get("full_page", False)
            skill.take_screenshot(name, full_page)
            return f"Screenshot taken: {name}"
            
        elif operation == "end_session":
            status = kwargs.get("status", "Completed")
            skill.end_session(status)
            return f"Browser session ended with status: {status}"
            
        else:
            return f"Unknown operation: {operation}"
    
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


async def create_web_testing_agents(use_group_chat: bool = True) -> Union[
    Tuple[AssistantAgent, AssistantAgent, AssistantAgent, CodeExecutorAgent, SelectorGroupChat], 
    Tuple[AssistantAgent, CodeExecutorAgent]
]:
    """
    Create and initialize web testing agents
    
    Args:
        use_group_chat: Whether to use SelectorGroupChat for better conversation control (default: True)
        
    Returns:
        If use_group_chat=True:
            Tuple[AssistantAgent, AssistantAgent, AssistantAgent, CodeExecutorAgent, SelectorGroupChat]
        If use_group_chat=False:
            Tuple[AssistantAgent, CodeExecutorAgent]
    """
    # Get model client
    model_client = LLMProvider().get_model_client()
    logger.info(f"LOG: Creating agents with model client")
    
    # Create the testing agent
    web_tester = AssistantAgent(
        name="web_tester",
        system_message=WEB_TESTER_PROMPT,
        model_client=model_client,
        tools=[execute_playwright_operation],
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
    code_executor = CodeExecutorAgent(
        name="code_executor",
        code_executor=LocalCommandLineCodeExecutor(
            work_dir=None,
            timeout=int(os.getenv('EXECUTION_TIMEOUT', '300'))  # 5 minutes default timeout
        ),
        description="An executor agent that runs Python code for test automation."
    )
    
    # Register the playwright tool with the web_tester agent
    web_tester.tools = [execute_playwright_operation]
    
    if use_group_chat:
        # Create termination conditions
        text_termination = TextMentionTermination("you can find the full test report at:")
        max_message_termination = MaxMessageTermination(30)  # Terminate after 30 messages
        termination = text_termination | max_message_termination
        
        # Create the group chat
        group_chat = SelectorGroupChat(
            agents=[web_tester, debug_agent, security_admin, code_executor],
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