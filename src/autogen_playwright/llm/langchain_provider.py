"""
LangChain provider for browser-use that leverages our existing LLM configuration.
This allows browser-use to use the same environment variables and configuration
as the rest of the framework.
"""
import os
import logging
from typing import Optional, Dict, Any, Union
import json
import httpx

from .config import LLMConfig

logger = logging.getLogger(__name__)

class LangChainProvider:
    """
    Provider for LangChain models that uses the same configuration
    as our LLMProvider for AutoGen.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LangChainProvider with configuration.
        
        Args:
            config: LLMConfig instance (will load from environment if None)
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or LLMConfig.from_env()
        self._set_provider_env_vars()
        
    def _set_provider_env_vars(self):
        """Map LLM_API_KEY to provider-specific environment variables"""
        provider_env_mapping = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'azure': 'AZURE_OPENAI_API_KEY',
            'cerebras': 'CEREBRAS_API_KEY'
        }
        
        if env_var := provider_env_mapping.get(self.config.provider):
            os.environ[env_var] = self.config.api_key
            self.logger.info(f"LOG:  Mapped LLM_API_KEY to {env_var}")
            # Debug log the first 4 chars of the mapped key
            self.logger.info(f"LOG:  {env_var}: {self.config.api_key[:4]}...")
        else:
            self.logger.warning(f"LOG:  No environment variable mapping found for provider: {self.config.provider}")
    
    def get_langchain_llm(self):
        """
        Get a LangChain LLM model based on the configuration.
        
        Returns:
            A LangChain LLM instance (OpenAI, Anthropic, etc.)
        """
        try:
            if self.config.provider == 'openai':
                from langchain_openai import ChatOpenAI
                import json
                
                # Enable debug logging for httpx
                httpx_logger = logging.getLogger("httpx")
                httpx_logger.setLevel(logging.DEBUG)
                
                model_name = self.config.model
                self.logger.info(f"Creating ChatOpenAI with model: {model_name}")
                self.logger.info(f"Using temperature: {self.config.temperature}")
                self.logger.info(f"Using request timeout: {self.config.request_timeout}")
                self.logger.info(f"OPENAI_API_KEY environment variable is set: {'OPENAI_API_KEY' in os.environ}")
                self.logger.info(f"OPENAI_API_KEY length: {len(os.getenv('OPENAI_API_KEY', ''))}")
                
                # Create a test request to verify the configuration
                test_request = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": "test"}],
                    "temperature": self.config.temperature
                }
                self.logger.info(f"Test request configuration: {json.dumps(test_request, indent=2)}")
                
                # Create the ChatOpenAI instance with explicit configuration
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=self.config.temperature,
                    request_timeout=self.config.request_timeout,
                    openai_api_key=os.getenv('OPENAI_API_KEY'),  # Explicitly pass the API key
                    max_retries=3,  # Limit retries to 3
                    streaming=False,  # Disable streaming to simplify error handling
                    verbose=True  # Enable verbose logging
                )
                
                # Test the LLM with a simple request
                try:
                    self.logger.info("Testing LLM with a simple request...")
                    response = llm.invoke("test")
                    self.logger.info(f"Test response: {response}")
                    
                    # Log the actual request that was made
                    if hasattr(llm, 'client') and hasattr(llm.client, '_last_request'):
                        self.logger.info(f"Last request made: {json.dumps(llm.client._last_request, indent=2)}")
                except Exception as e:
                    self.logger.error(f"Test request failed: {str(e)}")
                    if hasattr(e, 'response'):
                        self.logger.error(f"Response status: {e.response.status_code}")
                        self.logger.error(f"Response body: {e.response.text}")
                    raise
                
                self.logger.info("ChatOpenAI instance created and tested successfully")
                return llm
                
            elif self.config.provider == 'anthropic':
                from langchain_anthropic import ChatAnthropic
                
                # Map model names if needed
                model_mapping = {
                    'claude-2': 'claude-2',
                    'claude-3-opus': 'claude-3-opus-20240229',
                    'claude-3-sonnet': 'claude-3-sonnet-20240229',
                    'claude-3-haiku': 'claude-3-haiku-20240307'
                }
                
                model_name = model_mapping.get(self.config.model, self.config.model)
                
                self.logger.info(f"Creating ChatAnthropic with model: {model_name}")
                
                return ChatAnthropic(
                    model=model_name,
                    temperature=self.config.temperature,
                    timeout=self.config.request_timeout,
                    anthropic_api_key=self.config.api_key
                )
                
            elif self.config.provider == 'azure':
                from langchain_openai import AzureChatOpenAI
                
                self.logger.info(f"Creating AzureChatOpenAI with deployment: {self.config.model}")
                
                return AzureChatOpenAI(
                    deployment_name=self.config.model,
                    temperature=self.config.temperature,
                    request_timeout=self.config.request_timeout,
                    openai_api_key=self.config.api_key,
                    openai_api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2023-07-01-preview'),
                    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT', '')
                )
                
            elif self.config.provider == 'llama':
                from langchain_community.llms import LlamaCpp
                
                self.logger.info(f"Creating LlamaCpp with model path: {self.config.model}")
                
                return LlamaCpp(
                    model_path=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens or 2000,
                    verbose=True
                )
                
            else:
                raise ValueError(f"Unsupported provider for LangChain: {self.config.provider}")
                
        except ImportError as e:
            install_command = ""
            if self.config.provider == 'openai':
                install_command = "pip install langchain-openai"
            elif self.config.provider == 'anthropic':
                install_command = "pip install langchain-anthropic"
            elif self.config.provider == 'llama':
                install_command = "pip install llama-cpp-python"
                
            raise ImportError(
                f"Missing required packages for {self.config.provider} LangChain integration. "
                f"Please install with: {install_command}"
            ) from e
