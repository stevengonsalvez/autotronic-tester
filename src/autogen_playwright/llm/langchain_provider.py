"""
LangChain provider for browser-use that leverages our existing LLM configuration.
This allows browser-use to use the same environment variables and configuration
as the rest of the framework.
"""
import os
import logging
from typing import Optional, Dict, Any, Union

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
        self.config = config or LLMConfig.from_env()
        self._set_provider_env_vars()
        self.logger = logging.getLogger(__name__)
        
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
    
    def get_langchain_llm(self):
        """
        Get a LangChain LLM model based on the configuration.
        
        Returns:
            A LangChain LLM instance (OpenAI, Anthropic, etc.)
        """
        try:
            # Import here to make dependencies optional
            if self.config.provider == 'openai':
                from langchain_openai import ChatOpenAI
                
                # Map model names if needed
                model_mapping = {
                    'gpt-4': 'gpt-4',
                    'gpt-4-turbo': 'gpt-4-turbo-preview',
                    'gpt-4o': 'gpt-4o'
                }
                
                model_name = model_mapping.get(self.config.model, self.config.model)
                
                self.logger.info(f"Creating ChatOpenAI with model: {model_name}")
                
                return ChatOpenAI(
                    model=model_name,
                    temperature=self.config.temperature,
                    request_timeout=self.config.request_timeout
                )
                
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
