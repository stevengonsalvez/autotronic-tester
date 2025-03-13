"""
Example demonstrating how to use the SQLiteEventLogger for observability in AutoGen 0.4
"""
import os
import asyncio
import logging
from pathlib import Path
from autogen_core import CancellationToken
from autogen_core.events import register_listener
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_playwright.utils.common_utils import load_env_from_file
from autogen_playwright.ops.event_logger import SQLiteEventLogger
from autogen_playwright.ops.report_generator import ReportGenerator

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
        
        # Create and register the event logger
        db_path = Path("./runtime_logs/autogen_logs.db")
        event_logger = SQLiteEventLogger(db_path=db_path)
        
        # Register the event listener with AutoGen
        register_listener(event_logger)
        logger.info(f"Registered SQLiteEventLogger with database at {db_path}")
        
        # Import after environment variables are loaded
        from autogen_playwright import create_web_testing_agents, PlaywrightSkill
        
        # Create agents with loaded environment
        use_group_chat = os.getenv('USE_GROUP_CHAT', 'true').lower() == 'true'
        force_mode = os.getenv('FORCE_MODE', 'auto').lower()
        logger.info(f"Using group chat mode: {use_group_chat}")
        logger.info(f"Using force mode: {force_mode}")
        
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
            
            logger.info("Starting group chat...")
            stream = group_chat.run_stream(task=test_message, cancellation_token=cancellation_token)
            
            # Console UI for streaming the output
            await Console(stream)
            
            # Get the result for session ID
            result = await group_chat.run(test_message, cancellation_token=cancellation_token)
            
            # Extract session ID if available
            session_id = None
            if hasattr(result, "session_id"):
                session_id = result.session_id
            
        else:
            web_tester, code_executor = agents
            
            logger.info("Starting direct agent conversation...")
            
            # Use the web_tester to process the test message
            response = await web_tester.on_messages([TextMessage(content=test_message, source="user")], 
                                                  cancellation_token)
            
            # Pass the generated code to the code_executor
            logger.info("Passing generated code to code executor...")
            executor_response = await code_executor.on_messages(
                [response.chat_message],
                cancellation_token
            )
            
            # Extract session ID if available
            session_id = None
            if hasattr(response, "session_id"):
                session_id = response.session_id
        
        # Print session statistics
        logger.info("Test execution completed. Generating statistics...")
        event_logger.print_session_summary(session_id)
        
        # Generate HTML report
        logger.info("Generating HTML report...")
        report_generator = ReportGenerator(db_path=db_path)
        report_path = Path("./reports/autogen_report.html")
        report_generator.generate_html_report(report_path, session_id)
        logger.info(f"HTML report generated at {report_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to execute: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    os._exit(exit_code) 