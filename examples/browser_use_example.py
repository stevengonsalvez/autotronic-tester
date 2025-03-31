"""
Example script demonstrating the use of browser_use's Agent with AutoGen.

This example shows how to use browser_use as an alternative to Playwright
for browser automation in LLM-powered testing.
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
    """Run an example test using browser_use's Agent"""
    try:
        # Load environment variables
        load_dotenv()
        logger.info("Loaded environment variables")
        
        # Create BrowserUseSkill instance
        # You can specify custom Chrome path if needed:
        # chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'  # macOS
        # chrome_path = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'  # Windows
        # chrome_path = '/usr/bin/google-chrome'  # Linux
        
        # Get headless mode from environment variable, default to False
        headless_str = os.getenv('BROWSER_HEADLESS', 'false').lower()
        headless = headless_str == 'true'
        logger.info(f"Browser headless mode: {headless}")
        
        # Create screenshots directory
        screenshots_dir = Path("./screenshots")
        screenshots_dir.mkdir(exist_ok=True)
        
        skill = BrowserUseSkill(
            screenshot_dir=screenshots_dir,
            headless=headless,
            skip_test=True  # Skip the initial test that goes to Google
        )
        logger.info("Created BrowserUseSkill instance")
        
        # Set up the browser and agent
        await skill.setup()
        logger.info("Set up browser_use browser and agent")
        
        # Define test steps
        test_steps = [
            "Navigate to ee.co.uk",
            "Accept cookies in the OneTrust banner",
            "Hover over 'Broadband' in the global navigation menu",
            "click to 'explore broadband' within the submenu pop up on the hover",
            "Analyze and summarize the page content",
            "Then go and enter postcode as UB87PE in the postcode field and click continue",
            "Analyze and summarize the page"
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
        start_time = time.time()
        result = await skill.execute_task(task)
        end_time = time.time()
        
        logger.info(f"Task completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Result: {result}")
        
        # Wait for user input before closing
        input("Press Enter to close the browser...")
        
        # Clean up
        await skill.cleanup()
        logger.info("Resources cleaned up")
        
        return 0
    except Exception as e:
        logger.error(f"Error running test: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    # Run the EE example
    exit_code = asyncio.run(run_test_with_browser_use())
    os._exit(exit_code)
