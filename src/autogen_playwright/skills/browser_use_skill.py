"""
Browser automation skill using browser-use library.
"""
import os
import logging
import asyncio
from typing import Optional
from browser_use import Agent, Browser
from browser_use.browser.context import BrowserContextConfig
from langchain_community.callbacks.manager import get_openai_callback
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler

logger = logging.getLogger(__name__)

class TokenTrackingCallback(BaseCallbackHandler):
    """Callback handler for tracking token usage"""
    
    def __init__(self):
        self.successful_requests = 0
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_cost = 0.0
    
    def on_llm_end(self, response, **kwargs):
        """Handle the end of an LLM call"""
        if hasattr(response, 'usage'):
            usage = response.usage
            self.successful_requests += 1
            self.total_tokens += usage.total_tokens
            self.prompt_tokens += usage.prompt_tokens
            self.completion_tokens += usage.completion_tokens
            # Approximate cost calculation (may need adjustment based on model)
            self.total_cost += (usage.prompt_tokens * 0.00001 + usage.completion_tokens * 0.00003)

class BrowserUseSkill:
    """
    Skill for browser automation using browser-use library.
    """
    
    def __init__(self, headless: bool = True, chrome_path: Optional[str] = None, skip_test: bool = False):
        """
        Initialize the browser-use skill.
        
        Args:
            headless: Whether to run browser in headless mode
            chrome_path: Optional path to Chrome executable
            skip_test: Whether to skip the initial test task
        """
        self.headless = headless
        self.chrome_path = chrome_path
        self.skip_test = skip_test
        self.browser = None
        self.agent = None
        self.llm = None
        self.callback_handler = TokenTrackingCallback()
        
    async def setup(self):
        """Set up the browser-use agent"""
        try:
            # Set up OpenAI API key
            if not os.getenv("OPENAI_API_KEY"):
                os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY")
                logger.info("Set OPENAI_API_KEY from LLM_API_KEY")
            
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("No OpenAI API key found in environment variables")
            
            logger.info(f"API key available: {bool(os.getenv('OPENAI_API_KEY'))}")
            
            # Create ChatOpenAI instance as recommended by browser-use docs
            logger.info("Creating ChatOpenAI with gpt-4o model as recommended by browser-use docs")
            self.llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                callbacks=[self.callback_handler]
            )
            
            # Skip the full setup if requested
            if self.skip_test:
                logger.info("Skipping Agent creation and test task as requested")
                return
                
            # Create browser context configuration
            cookies_file = os.getenv("BROWSER_COOKIES_FILE")
            context_config = None
            
            if cookies_file and os.path.exists(cookies_file):
                logger.info(f"Loading cookies from: {cookies_file}")
                context_config = BrowserContextConfig(
                    cookies_file=cookies_file,
                    highlight_elements=True
                )
            
            # Create browser-use agent with initial test task
            logger.info("Creating Agent with test task")
            self.agent = Agent(
                task="Go to google.com",
                llm=self.llm,
                headless=self.headless,
                context_config=context_config
            )
            
            # Run the initial test task
            logger.info("Running initial test task")
            await self.agent.run()
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {e.__dict__}")
            raise
    
    async def execute_task(self, task):
        """
        Execute a task using the browser_use Agent.
        
        Args:
            task: The task to execute (string with instructions)
            
        Returns:
            The result of the agent's execution
        """
        logger.info(f"BrowserUseSkill executing task: {task}")
        
        try:
            # Lazy initialization of agent if it was skipped during setup
            if self.agent is None:
                logger.info("Creating Agent for first task")
                
                # Create browser context configuration
                cookies_file = os.getenv("BROWSER_COOKIES_FILE")
                context_config = None
                
                if cookies_file and os.path.exists(cookies_file):
                    logger.info(f"Loading cookies from: {cookies_file}")
                    context_config = BrowserContextConfig(
                        cookies_file=cookies_file,
                        highlight_elements=True
                    )
                
                self.agent = Agent(
                    task=task,
                    llm=self.llm,
                    headless=self.headless,
                    context_config=context_config
                )
            else:
                # Configure the agent with the new task
                self.agent.task = task
            
            # Execute the task
            logger.info("Executing task")
            result = await self.agent.run()
            
            # Log token usage after task completion
            logger.info(f"Token usage for task: {self.callback_handler.successful_requests} requests")
            logger.info(f"Total tokens: {self.callback_handler.total_tokens}")
            logger.info(f"Prompt tokens: {self.callback_handler.prompt_tokens}")
            logger.info(f"Completion tokens: {self.callback_handler.completion_tokens}")
            logger.info(f"Total cost (USD): ${self.callback_handler.total_cost:.6f}")
            
            logger.info(f"Task execution successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {e.__dict__}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise RuntimeError(f"Failed to execute task: {str(e)}") from e
            
    async def cleanup(self):
        """Clean up resources"""
        if self.agent:
            try:
                await self.agent.browser.close()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
                logger.error(f"Error type: {type(e)}")
                logger.error(f"Error details: {e.__dict__}")
