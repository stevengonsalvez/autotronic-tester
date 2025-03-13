import os
import logging
import tempfile
import functools
import json
from typing import Dict, Any, Optional, Callable, List, Union, AsyncGenerator
from .config import LLMConfig
from autogen_core.models import ChatCompletionClient
from autogen_ext.models.openai import OpenAIChatCompletionClient, AzureOpenAIChatCompletionClient
from autogen_ext.models.cache import ChatCompletionCache, CHAT_CACHE_VALUE_TYPE
from autogen_ext.cache_store.diskcache import DiskCacheStore
from diskcache import Cache
from abc import ABC, abstractmethod
import autogen
from autogen.agentchat.agent import Agent

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LLMCallLogger(ChatCompletionClient):
    """Wrapper around a ChatCompletionClient that logs calls to an event logger."""
    
    def __init__(self, client: ChatCompletionClient, event_logger: Any):
        self.client = client
        self.event_logger = event_logger
        self.logger = logging.getLogger(__name__)
        self.logger.info("LLMCallLogger initialized")
        # Cache model info
        self._model_info = {
            "function_calling": True,
            "vision": False,
            "max_tokens": 8192,
            "model": "gpt-4"
        }
        
    async def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Log the chat completion call and its result."""
        self.logger.info("LLMCallLogger.chat_completion called")
        result = await self.client.chat_completion(messages, **kwargs)
        
        # Extract token usage
        usage = result.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        self.logger.info(f"LLMCallLogger.chat_completion result: {result}")
        self.logger.info(f"LLMCallLogger.chat_completion usage: {usage}")
        
        # Log the event
        event_payload = {
            "messages": messages,
            "response": result,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "session_id": kwargs.get("session_id"),
            "agent_id": kwargs.get("agent_id")
        }
        
        self.logger.info(f"Logging LLM call: {prompt_tokens} prompt tokens, {completion_tokens} completion tokens")
        
        # Log the event using the event logger
        if hasattr(self.event_logger, 'log_event'):
            self.logger.info("Calling event_logger.log_event")
            self.event_logger.log_event("LLMCall", event_payload)
            self.logger.info("Called event_logger.log_event")
        else:
            self.logger.warning("event_logger does not have log_event method")
        
        return result
    
    async def chat_completion_stream(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream the chat completion and log the final result."""
        # Collect the full response
        full_response = {"content": ""}
        
        # Stream the response
        async for chunk in self.client.chat_completion_stream(messages, **kwargs):
            yield chunk
            
            # Update the full response
            if "content" in chunk and chunk["content"] is not None:
                full_response["content"] += chunk["content"]
        
        # Log the event after streaming is complete
        # Note: Token counts are approximate since we don't have exact counts from streaming
        prompt_tokens = len(json.dumps(messages)) // 4  # Rough estimate
        completion_tokens = len(full_response["content"]) // 4  # Rough estimate
        
        event_payload = {
            "messages": messages,
            "response": full_response,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "session_id": kwargs.get("session_id"),
            "agent_id": kwargs.get("agent_id")
        }
        
        self.logger.info(f"Logging streamed LLM call: ~{prompt_tokens} prompt tokens, ~{completion_tokens} completion tokens")
        
        # Log the event using the event logger
        if hasattr(self.event_logger, 'log_event'):
            self.event_logger.log_event("LLMCall", event_payload)
    
    async def create(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Delegate to the wrapped client."""
        self.logger.info("LLMCallLogger.create called")
        result = await self.client.create(messages, **kwargs)
        
        self.logger.info(f"LLMCallLogger.create result type: {type(result)}")
        
        # Extract token usage - handle both dict and object formats
        try:
            # Try to access usage as an attribute
            if hasattr(result, "usage"):
                usage = result.usage
                prompt_tokens = getattr(usage, "prompt_tokens", 0)
                completion_tokens = getattr(usage, "completion_tokens", 0)
            # Try to access as a dictionary
            elif isinstance(result, dict) and "usage" in result:
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
            else:
                # Fallback to approximation
                prompt_tokens = await self.count_tokens(str(messages))
                completion_tokens = await self.count_tokens(str(result))
                usage = {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}
                
            self.logger.info(f"LLMCallLogger.create usage: {usage}")
            
            # Convert result to a serializable format if needed
            response_dict = {}
            if hasattr(result, "__dict__"):
                # Try to convert object to dict
                response_dict = {k: v for k, v in result.__dict__.items() 
                               if not k.startswith('_') and not callable(v)}
            elif isinstance(result, dict):
                response_dict = result
            else:
                # Last resort, convert to string
                response_dict = {"content": str(result)}
            
            # Log the event
            event_payload = {
                "messages": messages,
                "response": response_dict,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "session_id": kwargs.get("session_id"),
                "agent_id": kwargs.get("agent_id")
            }
            
            self.logger.info(f"Logging LLM call from create: {prompt_tokens} prompt tokens, {completion_tokens} completion tokens")
            
            # Log the event using the event logger
            if hasattr(self.event_logger, 'log_event'):
                self.logger.info("Calling event_logger.log_event from create")
                self.event_logger.log_event("LLMCall", event_payload)
                self.logger.info("Called event_logger.log_event from create")
            else:
                self.logger.warning("event_logger does not have log_event method")
        except Exception as e:
            self.logger.error(f"Error processing LLM call result: {e}")
            
        return result
    
    async def create_stream(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Delegate to the wrapped client."""
        self.logger.info("LLMCallLogger.create_stream called")
        
        # Collect the entire response to estimate token usage
        full_response = ""
        async for chunk in self.client.create_stream(messages, **kwargs):
            # Try to extract delta content from different object types
            try:
                if hasattr(chunk, "delta"):
                    delta = chunk.delta
                    if hasattr(delta, "content") and delta.content:
                        full_response += delta.content
                elif isinstance(chunk, dict) and "delta" in chunk:
                    delta = chunk.get("delta", "")
                    if isinstance(delta, str):
                        full_response += delta
                    elif isinstance(delta, dict) and "content" in delta:
                        content = delta.get("content", "")
                        if content:
                            full_response += content
                
                self.logger.debug(f"Stream chunk type: {type(chunk)}")
            except Exception as e:
                self.logger.error(f"Error processing stream chunk: {e}")
            
            yield chunk
        
        try:
            # Approximate token count (this is not accurate but gives an estimate)
            prompt_tokens = await self.count_tokens(str(messages))
            completion_tokens = await self.count_tokens(full_response)
            
            self.logger.info(f"LLMCallLogger.create_stream completed with approx {prompt_tokens} prompt tokens, {completion_tokens} completion tokens")
            
            # Log the event
            event_payload = {
                "messages": messages,
                "response": {"content": full_response},
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "session_id": kwargs.get("session_id"),
                "agent_id": kwargs.get("agent_id"),
                "is_stream": True
            }
            
            # Log the event using the event logger
            if hasattr(self.event_logger, 'log_event'):
                self.logger.info("Calling event_logger.log_event from create_stream")
                self.event_logger.log_event("LLMCall", event_payload)
                self.logger.info("Called event_logger.log_event from create_stream")
            else:
                self.logger.warning("event_logger does not have log_event method")
        except Exception as e:
            self.logger.error(f"Error logging stream completion: {e}")
    
    async def count_tokens(self, messages: Union[List[Dict[str, Any]], str]) -> int:
        """Delegate to the wrapped client."""
        self.logger.info(f"LLMCallLogger.count_tokens called with type: {type(messages)}")
        try:
            if isinstance(messages, str):
                # Approximate token count for strings
                return len(messages.split()) * 4 // 3  # Rough approximation
            return await self.client.count_tokens(messages)
        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            # Fallback to a rough approximation
            if isinstance(messages, str):
                return len(messages.split()) * 4 // 3
            else:
                # For message lists, estimate based on content
                total = 0
                for msg in messages:
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        total += len(content.split()) * 4 // 3
                return total
    
    async def remaining_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Delegate to the wrapped client."""
        return await self.client.remaining_tokens(messages)
    
    async def total_usage(self) -> Dict[str, int]:
        """Delegate to the wrapped client."""
        return await self.client.total_usage()
    
    async def actual_usage(self) -> Dict[str, int]:
        """Delegate to the wrapped client."""
        return await self.client.actual_usage()
    
    async def capabilities(self) -> Dict[str, Any]:
        """Delegate to the wrapped client."""
        return await self.client.capabilities()
    
    @property
    def model_info(self) -> Dict[str, Any]:
        """Return model information."""
        return self._model_info

class LLMProvider:
    def __init__(self, config: Optional[LLMConfig] = None, event_logger: Optional[Any] = None):
        self.config = config or LLMConfig.from_env()
        self._set_provider_env_vars()
        self.logger = logging.getLogger(__name__)
        self.event_logger = event_logger
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
        
        # Wrap with logger if event_logger is provided
        if self.event_logger:
            self.logger.info("Wrapping model client with LLMCallLogger")
            model_client = LLMCallLogger(model_client, self.event_logger)
            
        return model_client