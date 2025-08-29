"""
OpenAI Provider Implementation for Unified Three-Tier Architecture

This module implements the unified three-tier architecture for OpenAI:
1. Auto-Integration Pattern (Magic): Automatic SDK interception
2. Wrapper Pattern (Best Practice): Clean wrapped client
3. Manual Recording Pattern (Manual Utility): Manual response parsing
"""

from typing import Any, Dict, List, Optional
import time

from loguru import logger

from ...core.providers_base import (
    BaseProvider, ProviderType, PatternType,
    ProviderRequest, ProviderResponse
)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available")


class OpenAIProvider(BaseProvider):
    """
    OpenAI provider implementation for the unified three-tier architecture.
    
    Supports all three patterns:
    - Auto-Integration: Monkey-patches OpenAI SDK methods
    - Wrapper: Provides clean MemoriOpenAI client
    - Manual Recording: Parses OpenAI responses for manual recording
    """
    
    def __init__(self, memori_instance, provider_type: ProviderType, **kwargs):
        """Initialize OpenAI provider."""
        super().__init__(memori_instance, provider_type, **kwargs)
        self._original_create_method = None
        self._auto_integration_active = False
        
    def _check_availability(self) -> bool:
        """Check if OpenAI is available."""
        return OPENAI_AVAILABLE
    
    # ========================
    # Auto-Integration Pattern (Magic)
    # ========================
    
    def setup_auto_integration(self) -> bool:
        """Set up OpenAI auto-integration by monkey-patching SDK methods."""
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI not available - cannot setup auto-integration")
            return False
            
        if self._auto_integration_active:
            logger.warning("OpenAI auto-integration already active")
            return True
        
        try:
            from openai.resources.chat.completions import Completions
            
            # Store original method
            self._original_create_method = Completions.create
            
            # Create intercepted method with closure to capture self
            provider_self = self
            
            def intercepted_create(completions_self, **kwargs):
                try:
                    # Use the pattern manager for consistent request handling
                    kwargs = provider_self.memori_instance.pattern_manager.handle_request(
                        ProviderType.OPENAI, PatternType.AUTO_INTEGRATION, kwargs
                    )
                    
                    # Call original method
                    response = provider_self._original_create_method(completions_self, **kwargs)
                    
                    # Use pattern manager for consistent response handling
                    if provider_self.memori_instance.is_enabled:
                        provider_self.memori_instance.pattern_manager.handle_response(
                            ProviderType.OPENAI, PatternType.AUTO_INTEGRATION, response, kwargs
                        )
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"OpenAI auto-integration failed: {e}")
                    # Fallback to original method
                    return provider_self._original_create_method(completions_self, **kwargs)
            
            # Replace the method
            Completions.create = intercepted_create
            
            self._auto_integration_active = True
            logger.info("OpenAI auto-integration setup successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup OpenAI auto-integration: {e}")
            return False
    
    def teardown_auto_integration(self) -> bool:
        """Tear down OpenAI auto-integration."""
        if not OPENAI_AVAILABLE:
            return False
            
        if not self._auto_integration_active:
            return True
        
        try:
            from openai.resources.chat.completions import Completions
            
            # Restore original method
            if self._original_create_method is not None:
                Completions.create = self._original_create_method
                self._original_create_method = None
            
            self._auto_integration_active = False
            logger.info("OpenAI auto-integration teardown successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to teardown OpenAI auto-integration: {e}")
            return False
    
    def is_auto_integration_active(self) -> bool:
        """Check if OpenAI auto-integration is active."""
        return self._auto_integration_active
    
    # ========================
    # Wrapper Pattern (Best Practice)
    # ========================
    
    def create_wrapped_client(self, **kwargs) -> Any:
        """Create a wrapped OpenAI client."""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available")
        
        try:
            return MemoriOpenAIClient(self, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create wrapped OpenAI client: {e}")
            raise
    
    # ========================
    # Manual Recording Pattern (Manual Utility)
    # ========================
    
    def parse_manual_response(self, response: Any, user_input: str = "", **kwargs) -> ProviderResponse:
        """Parse OpenAI response for manual recording."""
        try:
            # Extract content from response
            content = ""
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and choice.message:
                    content = choice.message.content or ""
                elif hasattr(choice, "text"):
                    content = choice.text or ""
            
            # Extract model
            model = getattr(response, "model", kwargs.get("model", "openai-unknown"))
            
            # Extract token usage
            tokens_used = 0
            if hasattr(response, "usage") and response.usage:
                tokens_used = getattr(response.usage, "total_tokens", 0)
            
            # Create metadata
            metadata = {
                "user_input": user_input,
                "manual_recording": True,
                "timestamp": time.time(),
                **kwargs
            }
            
            # Add detailed token usage if available
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                metadata.update({
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage, "completion_tokens", 0),
                })
            
            return ProviderResponse(
                content=content,
                model=model,
                provider_type=ProviderType.OPENAI,
                pattern_type=PatternType.MANUAL_RECORDING,
                metadata=metadata,
                original_response=response,
                tokens_used=tokens_used,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse OpenAI manual response: {e}")
            # Return minimal response to avoid breaking caller
            return ProviderResponse(
                content="[Error parsing response]",
                model="openai-unknown",
                provider_type=ProviderType.OPENAI,
                pattern_type=PatternType.MANUAL_RECORDING,
                metadata={"error": str(e), "user_input": user_input, **kwargs},
                original_response=response,
                tokens_used=0,
            )
    
    # ========================
    # Common Provider Methods
    # ========================
    
    def inject_context(self, request: ProviderRequest) -> ProviderRequest:
        """OpenAI-specific context injection (if needed)."""
        # The base UniversalContextInjector handles most cases
        # This method can be used for OpenAI-specific customizations
        return request
    
    def extract_user_input(self, request_data: Dict[str, Any]) -> str:
        """Extract user input from OpenAI request data."""
        try:
            messages = request_data.get("messages", [])
            # Find the last user message
            for message in reversed(messages):
                if message.get("role") == "user":
                    content = message.get("content", "")
                    
                    if isinstance(content, str):
                        return content
                    elif isinstance(content, list):
                        # Handle complex content (vision, multiple parts)
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                        return " ".join(text_parts)
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extracting OpenAI user input: {e}")
            return ""
    
    def parse_response(self, response: Any, request_data: Dict[str, Any]) -> ProviderResponse:
        """Parse OpenAI response into standardized format."""
        try:
            # Extract content
            content = ""
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and choice.message:
                    message = choice.message
                    if hasattr(message, "content") and message.content:
                        content = message.content
                    elif hasattr(message, "tool_calls") and message.tool_calls:
                        # Handle tool calls
                        tool_descriptions = []
                        for tool_call in message.tool_calls:
                            if hasattr(tool_call, "function"):
                                func_name = tool_call.function.name
                                func_args = tool_call.function.arguments
                                tool_descriptions.append(f"Called {func_name} with {func_args}")
                        content = "[Tool calls: " + "; ".join(tool_descriptions) + "]"
                elif hasattr(choice, "text"):
                    content = choice.text or ""
            
            # Extract model
            model = request_data.get("model", "openai-unknown")
            if hasattr(response, "model"):
                model = response.model
            
            # Extract token usage
            tokens_used = 0
            if hasattr(response, "usage") and response.usage:
                tokens_used = getattr(response.usage, "total_tokens", 0)
            
            # Create metadata
            metadata = {
                "original_request": request_data,
                "timestamp": time.time(),
            }
            
            # Add request metadata
            if "temperature" in request_data:
                metadata["temperature"] = request_data["temperature"]
            if "max_tokens" in request_data:
                metadata["max_tokens"] = request_data["max_tokens"]
            if "tools" in request_data:
                metadata["has_tools"] = True
                metadata["tool_count"] = len(request_data["tools"])
            
            # Add response metadata
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "finish_reason"):
                    metadata["finish_reason"] = choice.finish_reason
            
            # Add detailed token usage
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                metadata.update({
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage, "completion_tokens", 0),
                })
            
            return ProviderResponse(
                content=content,
                model=model,
                provider_type=ProviderType.OPENAI,
                pattern_type=PatternType.AUTO_INTEGRATION,  # Will be overridden by caller
                metadata=metadata,
                original_response=response,
                tokens_used=tokens_used,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            # Return minimal response to avoid breaking caller
            return ProviderResponse(
                content="[Error parsing response]",
                model="openai-unknown",
                provider_type=ProviderType.OPENAI,
                pattern_type=PatternType.AUTO_INTEGRATION,
                metadata={"error": str(e), "original_request": request_data},
                original_response=response,
                tokens_used=0,
            )


class MemoriOpenAIClient:
    """
    Wrapped OpenAI client for the Wrapper Pattern (Best Practice).
    
    This provides a clean, drop-in replacement for the OpenAI client
    that automatically records conversations through the unified architecture.
    """
    
    def __init__(self, provider: OpenAIProvider, **kwargs):
        """Initialize wrapped OpenAI client."""
        self.provider = provider
        self.memori_instance = provider.memori_instance
        
        # Create actual OpenAI client
        self._client = openai.OpenAI(**kwargs)
        
        # Create wrapped interfaces
        self.chat = self._create_chat_wrapper()
        self.completions = self._create_completions_wrapper()
        
        # Pass through other attributes
        for attr in dir(self._client):
            if not attr.startswith("_") and attr not in ["chat", "completions"]:
                setattr(self, attr, getattr(self._client, attr))
    
    def _create_chat_wrapper(self):
        """Create wrapped chat interface."""
        
        class ChatWrapper:
            def __init__(self, client, provider):
                self._client = client
                self.provider = provider
                self.completions = CompletionsWrapper(client, provider)
        
        class CompletionsWrapper:
            def __init__(self, client, provider):
                self._client = client
                self.provider = provider
            
            def create(self, **kwargs):
                try:
                    # Use pattern manager for consistent request handling
                    kwargs = self.provider.memori_instance.pattern_manager.handle_request(
                        ProviderType.OPENAI, PatternType.WRAPPER, kwargs
                    )
                    
                    # Make the actual API call
                    response = self._client.chat.completions.create(**kwargs)
                    
                    # Use pattern manager for consistent response handling
                    if self.provider.memori_instance.is_enabled:
                        self.provider.memori_instance.pattern_manager.handle_response(
                            ProviderType.OPENAI, PatternType.WRAPPER, response, kwargs
                        )
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"OpenAI wrapper failed: {e}")
                    raise
        
        return ChatWrapper(self._client, self.provider)
    
    def _create_completions_wrapper(self):
        """Create wrapped completions interface (legacy)."""
        
        class CompletionsWrapper:
            def __init__(self, client, provider):
                self._client = client
                self.provider = provider
            
            def create(self, **kwargs):
                try:
                    # Use pattern manager for consistent request handling
                    kwargs = self.provider.memori_instance.pattern_manager.handle_request(
                        ProviderType.OPENAI, PatternType.WRAPPER, kwargs
                    )
                    
                    # Make the actual API call
                    response = self._client.completions.create(**kwargs)
                    
                    # Use pattern manager for consistent response handling
                    if self.provider.memori_instance.is_enabled:
                        self.provider.memori_instance.pattern_manager.handle_response(
                            ProviderType.OPENAI, PatternType.WRAPPER, response, kwargs
                        )
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"OpenAI wrapper failed: {e}")
                    raise
        
        return CompletionsWrapper(self._client, self.provider)