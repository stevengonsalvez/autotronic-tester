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
                 headless: bool = False):
        """
        Initialize BrowserUseSkill
        
        Args:
            chrome_path: Path to Chrome executable (defaults to system default)
            screenshot_dir: Directory to save screenshots (defaults to ./screenshots)
            headless: Whether to run browser in headless mode (defaults to False)
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
        
    async def setup(self):
        """Set up the browser_use browser and agent"""
        # Configure browser
        browser_config = {}
        if self.chrome_path:
            browser_config['chrome_instance_path'] = self.chrome_path
            
        # Add headless option if specified
        browser_config['headless'] = self.headless
        
        # Get screenshot directory
        browser_config['screenshot_dir'] = str(self.screenshot_dir)
        
        # Create browser instance
        self.browser = self.Browser(
            config=self.BrowserConfig(**browser_config)
        )
        
        # Create LLM instance for the agent using our provider
        llm_provider = LangChainProvider()
        llm = llm_provider.get_langchain_llm()
        
        # Create agent (without a task yet)
        self.agent = self.Agent(
            task="", 
            llm=llm,
            browser=self.browser
        )
        
        logger.info("Browser and agent set up successfully")
        return "Browser and agent set up successfully"
    
    async def execute_task(self, task: str):
        """
        Execute a task using the browser_use agent
        
        Args:
            task: Natural language description of the task to perform
            
        Returns:
            Results of the task execution
        """
        if not self.agent:
            await self.setup()
        
        # Update the agent's task
        self.agent.task = task
        
        # Run the agent with progress logging
        logger.info(f"Starting browser-use task execution: {task[:100]}...")
        result = await self.agent.run()
        logger.info("Browser-use task execution completed")
        
        return result
    
    async def cleanup(self):
        """Close the browser and clean up resources"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.agent = None
            logger.info("Browser closed and resources cleaned up")
        return "Browser closed and resources cleaned up"
