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
        
        # Force code generation mode
        os.environ['FORCE_MODE'] = 'code_generation'
        logger.info("Setting FORCE_MODE=code_generation")
        
        # Import after environment variables are loaded
        from autogen_playwright import create_web_testing_agents, PlaywrightSkill
        
        # Create agents with loaded environment
        use_group_chat = os.getenv('USE_GROUP_CHAT', 'true').lower() == 'true'
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
        
        # Execute based on group chat mode
        if use_group_chat:
            web_tester, debug_agent, security_admin, code_executor, group_chat = agents
            
            logger.info("Starting group chat with code_generation mode...")
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
        
        else:
            web_tester, code_executor = agents
            
            logger.info("Starting direct agent conversation with code_generation mode...")
            
            # Use the web_tester to process the test message
            response = await web_tester.on_messages([TextMessage(content=test_message, source="user")], 
                                                  cancellation_token)
            logger.info("Web tester response:")
            logger.info("-" * 80)
            logger.info(format_code_for_logs(response.chat_message.content))
            logger.info("-" * 80)
            
            # Pass the generated code to the code_executor
            logger.info("Passing generated code to code executor...")
            executor_response = await code_executor.on_messages(
                [response.chat_message],
                cancellation_token
            )
            logger.info("Code execution completed with response:")
            logger.info("-" * 80)
            logger.info(format_code_for_logs(executor_response.chat_message.content))
            logger.info("-" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to execute: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    os._exit(exit_code) 