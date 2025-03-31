"""
BrowserUse skill for automating browsers through the browser_use library.
This is an alternative to PlaywrightSkill using the browser_use agent directly.
"""
import os
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from ..llm.langchain_provider import LangChainProvider

logger = logging.getLogger(__name__)

class BrowserUseSkill:
    """
    Skill for interacting with browser_use SDK.
    
    This provides browser automation capabilities using browser_use's Agent,
    which can directly handle natural language instructions.
    """
    
    def __init__(self, 
                 chrome_path: Optional[str] = None, 
                 screenshot_dir: Optional[Path] = None,
                 headless: bool = False,
                 skip_test: bool = False):
        """
        Initialize BrowserUseSkill
        
        Args:
            chrome_path: Path to Chrome executable (defaults to system default)
            screenshot_dir: Directory to save screenshots (defaults to ./screenshots)
            headless: Whether to run browser in headless mode (defaults to False)
            skip_test: Whether to skip the initial test task (defaults to False)
        """
        try:
            # Import here to make dependency optional
            from browser_use import Agent, Browser, BrowserConfig
            
            self.Agent = Agent
            self.Browser = Browser
            self.BrowserConfig = BrowserConfig
        except ImportError:
            raise ImportError(
                "browser_use package is required. Install with: pip install browser-use langchain-openai"
            )
            
        self.chrome_path = chrome_path
        self.headless = headless
        self.browser = None
        self.agent = None
        self.screenshot_dir = screenshot_dir or Path('./screenshots')
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.skip_test = skip_test
        
    async def setup(self):
        """Set up the browser_use browser and agent"""
        # Configure browser
        browser_config = {}
        if self.chrome_path:
            browser_config['chrome_instance_path'] = self.chrome_path
            
        # Add headless option if specified
        browser_config['headless'] = self.headless
        
        # Create browser instance
        self.browser = self.Browser(
            config=self.BrowserConfig(**browser_config)
        )
        
        # Create LLM directly following browser-use documentation pattern
        from langchain_openai import ChatOpenAI
        import os
        
        # Get API key from environment
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            # Try to get from our custom environment variable
            llm_api_key = os.getenv('LLM_API_KEY')
            if llm_api_key:
                os.environ['OPENAI_API_KEY'] = llm_api_key
                logger.info("Set OPENAI_API_KEY from LLM_API_KEY")
                openai_api_key = llm_api_key
        
        logger.info(f"API key available: {bool(openai_api_key)}")
        logger.info(f"API key length: {len(openai_api_key or '')}")
        
        # Create LLM instance directly as recommended in browser-use docs
        logger.info("Creating ChatOpenAI with gpt-4o model as recommended by browser-use docs")
        from langchain.callbacks import get_openai_callback
        
        # Store the callback for token tracking
        self.callback_manager = get_openai_callback()
        
        # Create LLM with callback handler for token tracking
        llm = ChatOpenAI(
            model="gpt-4o",  # Use their recommended model
            temperature=0.0  # Lower temperature for more deterministic responses
        )
        
        # Create agent (without a task yet)
        self.agent = self.Agent(
            task="", 
            llm=llm,
            browser=self.browser
        )
        
        # Test the agent with a simple task
        try:
            # Log the agent's configuration
            logger.info("Agent configuration:")
            logger.info(f"LLM type: {type(self.agent.llm)}")
            logger.info(f"LLM model: {getattr(self.agent.llm, 'model', 'unknown')}")
            
            if not self.skip_test:
                # Run a test task if not skipped
                logger.info("Testing agent with a simple task...")
                self.agent.task = "Go to google.com"
                test_result = await self.agent.run()
                logger.info(f"Test task result: {test_result}")
            else:
                logger.info("Skipping initial test task")
                
        except Exception as e:
            logger.error(f"Test task failed: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
        
        logger.info("Browser and agent set up successfully")
        return "Browser and agent set up successfully"
    
    async def execute_task(self, task):
        """
        Execute a task using the browser_use Agent.
        
        Args:
            task: The task to execute (string with instructions)
            
        Returns:
            The result of the agent's execution
        """
        logger.info(f"BrowserUseSkill executing task: {task}")
        
        # Configure the agent with the new task
        self.agent.task = task
        
        # Set max retries for execution
        max_retries = 3
        retry_count = 0
        
        # Try to execute the task with retries
        while retry_count < max_retries:
            try:
                # Use the callback manager to track token usage
                with self.callback_manager:
                    # Execute the task
                    logger.info(f"Executing task (attempt {retry_count + 1}/{max_retries})")
                    result = await self.agent.run()
                
                # Log token usage after task completion
                logger.info(f"Token usage for task: {self.callback_manager.successful_requests} requests")
                logger.info(f"Total tokens: {self.callback_manager.total_tokens}")
                logger.info(f"Prompt tokens: {self.callback_manager.prompt_tokens}")
                logger.info(f"Completion tokens: {self.callback_manager.completion_tokens}")
                logger.info(f"Total cost (USD): ${self.callback_manager.total_cost:.6f}")
                
                logger.info(f"Task execution successful: {result}")
                return result
            except Exception as e:
                retry_count += 1
                logger.error(f"Error executing task (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    # Wait before retrying
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # Max retries reached, raise the error
                    raise RuntimeError(f"Failed to execute task after {max_retries} attempts. Last error: {str(e)}") from e
    
    async def cleanup(self):
        """Close the browser and clean up resources"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.agent = None
            logger.info("Browser closed and resources cleaned up")
        return "Browser closed and resources cleaned up"
