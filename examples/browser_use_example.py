"""
Example script demonstrating the use of browser_use's Agent with AutoGen.

This example shows how to use browser_use as an alternative to Playwright
for browser automation in LLM-powered testing.

Environment Variables:
    OPENAI_API_KEY (required): Your OpenAI API key
    LLM_API_KEY (alternative): Alternative way to provide OpenAI API key
    BROWSER_HEADLESS: Set to 'true' to run browser in headless mode (default: false)
    BROWSER_COOKIES_FILE: Path to JSON file containing cookies (e.g., ./examples/cookies/cookies.json)
"""
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to the path
import sys
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

# Import BrowserUseSkill
from src.autogen_playwright.skills.browser_use_skill import BrowserUseSkill

async def run_test_with_browser_use():
    """Run a test using browser-use Agent with AutoGen"""
    try:
        # Load environment variables
        load_dotenv()
        logger.info("Loaded environment variables")
        
        # Get headless mode from environment
        headless = os.getenv('BROWSER_HEADLESS', 'false').lower() == 'true'
        logger.info(f"Browser headless mode: {headless}")
        
        # Set the cookies file path
        cookies_file = str(Path(__file__).parent / "cookies" / "cookies.json")
        os.environ["BROWSER_COOKIES_FILE"] = cookies_file
        if os.path.exists(cookies_file):
            logger.info(f"Using cookies file at: {cookies_file}")
        else:
            logger.warning(f"Cookies file not found at: {cookies_file}")
        
        # Create browser-use skill
        skill = BrowserUseSkill(
            headless=headless,
            skip_test=True  # Skip the initial test task
        )
        
        # Set up the skill
        await skill.setup()
        
        # Define test steps
        test_steps = [
            "Navigate to ee.co.uk",
            "Check if cookie consent banner appears and accept if it does",
            "Click on 'Check Coverage' button",
            "Enter postcode UB87PE",
            "Click 'Check Coverage' button",
            "Wait for results to load",
            "Take a screenshot of the results"
        ]
        
        # Format steps as a single task
        task = "\n".join([f"{i+1}. {step}" for i, step in enumerate(test_steps)])
        task = f"""Execute the following test steps EXACTLY as they are written, without searching for any information or visiting Google first. Start directly with step 1:
{task}

IMPORTANT: DO NOT visit Google or search for any information first. Begin IMMEDIATELY with step 1 - navigating to ee.co.uk.
Please take screenshots at each step. Make sure to capture evidence of each important action.
"""
        
        logger.info(f"Executing task:\n{task}")
        
        # Execute the task
        result = await skill.execute_task(task)
        
        # Clean up
        await skill.cleanup()
        
        logger.info(f"Test completed successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error running test: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    # Run the EE example
    exit_code = asyncio.run(run_test_with_browser_use())
    if exit_code == 0:
        logger.info("Test completed successfully")
    else:
        logger.error(f"Test failed with exit code: {exit_code}")
    os._exit(exit_code)
