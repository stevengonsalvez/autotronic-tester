import os
import logging
import tempfile
from typing import Dict, Any, Optional
from .config import LLMConfig
from autogen_core.models import ChatCompletionClient
from autogen_ext.models.openai import OpenAIChatCompletionClient, AzureOpenAIChatCompletionClient
from autogen_ext.models.cache import ChatCompletionCache, CHAT_CACHE_VALUE_TYPE
from autogen_ext.cache_store.diskcache import DiskCacheStore
from diskcache import Cache

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LLMProvider:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self._set_provider_env_vars()
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"LOG:  Initializing LLM with provider: {self.config.provider}, model: {self.config.model}")
        
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
    
    def get_model_client(self) -> ChatCompletionClient:
        """
        Create and return a model client based on the configuration.
        
        Returns:
            ChatCompletionClient: The configured model client
        """
        # Base parameters common to all providers
        base_params = {
            "temperature": self.config.temperature,
            "timeout": self.config.request_timeout,
            "seed": self.config.cache_seed,
        }
        
        if self.config.max_tokens:
            base_params["max_tokens"] = self.config.max_tokens
        
        # Create the appropriate model client based on provider
        if self.config.provider == 'openai':
            model_client = OpenAIChatCompletionClient(
                model=self.config.model,
                api_key=self.config.api_key,
                **base_params
            )
        elif self.config.provider == 'azure':
            model_client = AzureOpenAIChatCompletionClient(
                azure_deployment=self.config.model,
                api_key=self.config.api_key,
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT', ''),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2023-07-01-preview'),
                **base_params
            )
        else:
            # For other providers, use a generic component config
            # This would need to be expanded for other supported providers
            provider_map = {
                'anthropic': "AnthropicChatCompletionClient",
                'cerebras': "CerebrasChatCompletionClient"
            }
            
            provider_class = provider_map.get(self.config.provider)
            if not provider_class:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
                
            config = {
                "provider": provider_class,
                "config": {
                    "model": self.config.model,
                    "api_key": self.config.api_key,
                    **base_params
                }
            }
            
            model_client = ChatCompletionClient.load_component(config)
        
        # Add cache if enabled
        if self.config.cache_enable:
            cache_path = self.config.cache_path or tempfile.gettempdir()
            self.logger.info(f"LOG:  Using cache path: {cache_path}")
            
            # Create cache store
            cache_store = DiskCacheStore[CHAT_CACHE_VALUE_TYPE](
                Cache(cache_path)
            )
            
            # Wrap the model client with cache
            model_client = ChatCompletionCache(
                model_client,
                cache_store
            )
            
            if self.config.cache_seed is not None:
                self.logger.info(f"LOG:  Using cache seed: {self.config.cache_seed}")
        else:
            self.logger.warning("Cache is disabled!")
            
        return model_client