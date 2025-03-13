import os
import asyncio
import logging
from pathlib import Path
from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_playwright.utils.common_utils import load_env_from_file, format_code_for_logs
from autogen_playwright.ops.event_logger import SQLiteEventLogger
from autogen_playwright.ops.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_test(test_steps=None):
    try:
        logger.info("Starting test execution...")
        
        # Create the event logger but don't register it globally
        db_path = Path("./runtime_logs/autogen_logs.db")
        event_logger = SQLiteEventLogger(db_path=db_path)
        logger.info(f"Created SQLiteEventLogger with database at {db_path}")
        
        # Import after environment variables are loaded
        from autogen_playwright import create_web_testing_agents, PlaywrightSkill
        
        # Create agents with loaded environment
        use_group_chat = os.getenv('USE_GROUP_CHAT', 'true').lower() == 'true'
        force_mode = os.getenv('FORCE_MODE', 'auto').lower()
        logger.info(f"LOG: Using group chat mode: {use_group_chat}")
        logger.info(f"LOG: Using force mode: {force_mode}")
        
        agents = await create_web_testing_agents(use_group_chat=use_group_chat)
        
        # Default test steps if none provided
        default_steps = [
            "Navigate to ee.co.uk",
            "Accept cookies in the OneTrust banner",
            "Hover over 'Broadband' in the global navigation menu",
            "click to 'explore broadband' within the submenu pop up on the hover",
            "Analyze and summarize the page content",
            "Then go and enter postcode as UB87PE in the postcode field and click continue",
            "Analyze and summarize the page"
        ]
        
        steps_to_use = test_steps if test_steps else default_steps
        steps_formatted = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps_to_use))
        
        test_message = f"""
        Execute the following test scenario:
        
        Test Scenario: EE Broadband Page Navigation and Validation
        
        Steps:
        {steps_formatted}
        
        Important:
        - Maximum 5 retries for any action
        - Take screenshots at key steps
        - Provide detailed error information if steps fail
        - Generate a test summary at the end
        """
        
        try:
            logger.info("Initiating test with test message...")
            
            # Create cancellation token for potential cancellation
            cancellation_token = CancellationToken()
            
            # Track session ID for observability
            session_id = None
            
            # Initiate test based on mode
            if use_group_chat:
                web_tester, debug_agent, security_admin, code_executor, group_chat = agents
                
                # Run the group chat with the test message
                logger.info("Starting group chat for test execution...")
                
                # Log information about the force mode
                force_mode = os.getenv('FORCE_MODE', 'auto').lower()
                if force_mode == 'code_generation':
                    logger.info("Running in code_generation mode: Agent was instructed to generate complete Python code")
                elif force_mode == 'tool_usage':
                    logger.info("Running in tool_usage mode: Agent was instructed to use tools directly")
                else:
                    logger.info("Running in auto mode: Agent decided whether to use tools or generate code")
                
                stream = group_chat.run_stream(task=test_message, cancellation_token=cancellation_token)
                
                # Console UI for streaming the output
                await Console(stream)
                
                # Retrieve the result for any post-processing
                result = await group_chat.run(test_message, cancellation_token=cancellation_token)
                logger.info(f"Group chat completed with {len(result.messages)} messages")
                
                # Extract session ID if available
                if hasattr(result, "session_id"):
                    session_id = result.session_id
                
                # Log the last message from the conversation for better visibility
                if result.messages:
                    last_message = result.messages[-1]
                    logger.info(f"Final message from {last_message.source}:")
                    logger.info("-" * 80)
                    logger.info(format_code_for_logs(last_message.content))
                    logger.info("-" * 80)
                
            else:
                web_tester, code_executor = agents
                
                # For simpler implementation, just have a conversation between the two agents
                logger.info("Starting direct agent conversation for test execution...")
                
                # Use the web_tester to process the test message
                response = await web_tester.on_messages([TextMessage(content=test_message, source="user")], 
                                                      cancellation_token)
                
                # Extract session ID if available
                if hasattr(response, "session_id"):
                    session_id = response.session_id
                
                logger.info("Web tester response:")
                logger.info("-" * 80)
                logger.info(format_code_for_logs(response.chat_message.content))
                logger.info("-" * 80)
                
                # Now pass the generated code to the code_executor
                logger.info("Passing generated code to code executor...")
                
                # Log information about the force mode
                force_mode = os.getenv('FORCE_MODE', 'auto').lower()
                if force_mode == 'code_generation':
                    logger.info("Running in code_generation mode: Agent was instructed to generate complete Python code")
                elif force_mode == 'tool_usage':
                    logger.info("Running in tool_usage mode: Agent was instructed to use tools directly")
                else:
                    logger.info("Running in auto mode: Agent decided whether to use tools or generate code")
                
                executor_response = await code_executor.on_messages(
                    [response.chat_message],
                    cancellation_token
                )
                logger.info("Code execution completed with response:")
                logger.info("-" * 80)
                logger.info(format_code_for_logs(executor_response.chat_message.content))
                logger.info("-" * 80)
            
            # Generate observability reports
            logger.info("Test execution completed. Generating statistics...")
            
            # Print session statistics
            if session_id:
                logger.info(f"Session ID: {session_id}")
                event_logger.print_session_summary(session_id)
                
                # Generate HTML report
                logger.info("Generating HTML report...")
                report_generator = ReportGenerator(db_path=db_path)
                report_path = Path("./reports/autogen_report.html")
                report_generator.generate_html_report(report_path, session_id)
                logger.info(f"HTML report generated at {report_path}")
            else:
                logger.info("No session ID available, generating overall statistics")
                event_logger.print_session_summary()
                
                # Generate HTML report for all sessions
                logger.info("Generating HTML report for all sessions...")
                report_generator = ReportGenerator(db_path=db_path)
                report_path = Path("./reports/autogen_overall_report.html")
                report_generator.generate_html_report(report_path)
                logger.info(f"HTML report generated at {report_path}")
                
            return True
                
        except Exception as e:
            logger.error(f"Test execution exception: {str(e)}", exc_info=True)
            return False
            
    except Exception as e:
        logger.error(f"Test setup failed: {str(e)}", exc_info=True)
        print(f"Test setup failed: {str(e)}")
        return False

async def main():
    try:
        # Load environment variables
        env_path = load_env_from_file()
        
        logger.info(f"LOG:  Environment loaded from: {env_path}")
        logger.info(f"LOG:  Current working directory: {os.getcwd()}")
        logger.info(f"LOG:  Environment variables after loading:")
        logger.info(f"LOG:  LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
        logger.info(f"LOG:  LLM_MODEL: {os.getenv('LLM_MODEL')}")
        logger.info(f"LOG:  BROWSER_HEADLESS: {os.getenv('BROWSER_HEADLESS', 'not set')}")
        
        # Example of how to pass custom steps
        custom_steps = os.getenv('TEST_STEPS')
        if custom_steps:
            try:
                import json
                steps = json.loads(custom_steps)
            except json.JSONDecodeError:
                logger.warning("Invalid TEST_STEPS format, using default steps")
                steps = None
        else:
            steps = None
            
        success = await run_test(test_steps=steps)
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Failed to initialize: {str(e)}", exc_info=True)
        print(f"Failed to initialize: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    os._exit(exit_code)