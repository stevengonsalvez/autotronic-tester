import os
import asyncio
import logging
from pathlib import Path
from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_playwright.utils.common_utils import load_env_from_file, format_code_for_logs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Load environment variables
        env_path = load_env_from_file()
        logger.info(f"Environment loaded from: {env_path}")
        
        # Force tool usage mode
        os.environ['FORCE_MODE'] = 'tool_usage'
        logger.info("Setting FORCE_MODE=tool_usage")
        
        # Import after environment variables are loaded
        from autogen_playwright import create_web_testing_agents, PlaywrightSkill
        
        # Create agents with loaded environment
        # Note: For tool_usage mode, group chat is recommended
        os.environ['USE_GROUP_CHAT'] = 'true'
        use_group_chat = True
        logger.info(f"Using group chat mode: {use_group_chat}")
        
        agents = await create_web_testing_agents(use_group_chat=use_group_chat)
        
        # Simple test scenario
        test_message = """
        Execute the following test scenario:
        
        Test Scenario: Simple Google Search
        
        Steps:
        1. Navigate to google.com
        2. Accept cookies if prompted
        3. Search for "AutoGen framework"
        4. Verify search results appear
        """
        
        # Create cancellation token for potential cancellation
        cancellation_token = CancellationToken()
        
        # In tool_usage mode, we should use group chat
        web_tester, debug_agent, security_admin, code_executor, group_chat = agents
        
        logger.info("Starting group chat with tool_usage mode...")
        stream = group_chat.run_stream(task=test_message, cancellation_token=cancellation_token)
        
        # Console UI for streaming the output
        await Console(stream)
        
        # Log the final result
        result = await group_chat.run(test_message, cancellation_token=cancellation_token)
        logger.info(f"Group chat completed with {len(result.messages)} messages")
        
        # Log the last message from the conversation for better visibility
        if result.messages:
            last_message = result.messages[-1]
            logger.info(f"Final message from {last_message.source}:")
            logger.info("-" * 80)
            logger.info(format_code_for_logs(last_message.content))
            logger.info("-" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to execute: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    os._exit(exit_code) 