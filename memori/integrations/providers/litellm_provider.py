"""
LiteLLM Provider Implementation for Unified Three-Tier Architecture

This module implements the unified three-tier architecture for LiteLLM:
1. Auto-Integration Pattern (Magic): Native callback system
2. Wrapper Pattern (Best Practice): Clean wrapped interface
3. Manual Recording Pattern (Manual Utility): Manual response parsing

LiteLLM is special because it provides a universal interface to many LLM providers,
so this provider serves as both a direct LiteLLM integration and a fallback for
other providers that use LiteLLM under the hood.
"""

from typing import Any, Dict, List, Optional
import time

from loguru import logger

from ...core.providers_base import (
    BaseProvider, ProviderType, PatternType,
    ProviderRequest, ProviderResponse
)

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logger.warning("LiteLLM package not available")


class LiteLLMProvider(BaseProvider):
    """
    LiteLLM provider implementation for the unified three-tier architecture.
    
    LiteLLM is unique because it provides access to many different LLM providers
    through a single interface. This provider handles:
    - Auto-Integration: LiteLLM native callback system
    - Wrapper: Provides clean wrapped completion function
    - Manual Recording: Parses LiteLLM responses for manual recording
    
    This provider can work with any model that LiteLLM supports, including
    OpenAI, Anthropic, Cohere, AI21, and many others.
    """
    
    def __init__(self, memori_instance, provider_type: ProviderType, **kwargs):
        """Initialize LiteLLM provider."""
        super().__init__(memori_instance, provider_type, **kwargs)
        self._callback_registered = False
        self._original_callbacks = None
        self._original_completion_function = None
        
    def _check_availability(self) -> bool:
        """Check if LiteLLM is available."""
        return LITELLM_AVAILABLE
    
    # ========================
    # Auto-Integration Pattern (Magic)
    # ========================
    
    def setup_auto_integration(self) -> bool:
        """Set up LiteLLM auto-integration using native callback system."""
        if not LITELLM_AVAILABLE:
            logger.error("LiteLLM not available - cannot setup auto-integration")
            return False
            
        if self._callback_registered:
            logger.warning("LiteLLM auto-integration already active")
            return True
        
        try:
            # Store original callbacks for restoration
            self._original_callbacks = getattr(litellm, 'success_callback', [])
            
            # Register our success callback
            if not hasattr(litellm, 'success_callback'):
                litellm.success_callback = []
            elif not isinstance(litellm.success_callback, list):
                litellm.success_callback = [litellm.success_callback]
            
            # Add our callback function
            litellm.success_callback.append(self._litellm_success_callback)
            
            # Set up context injection by wrapping the completion function
            if self.memori_instance.conscious_ingest or self.memori_instance.auto_ingest:
                self._setup_context_injection()
            
            self._callback_registered = True
            logger.info("LiteLLM auto-integration setup successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup LiteLLM auto-integration: {e}")
            return False
    
    def teardown_auto_integration(self) -> bool:
        """Tear down LiteLLM auto-integration."""
        if not LITELLM_AVAILABLE:
            return False
            
        if not self._callback_registered:
            return True
        
        try:
            # Remove our callback
            if hasattr(litellm, 'success_callback') and isinstance(litellm.success_callback, list):
                # Remove all instances of our callback
                litellm.success_callback = [
                    cb for cb in litellm.success_callback 
                    if cb != self._litellm_success_callback
                ]
                
                # If no callbacks left, restore original state
                if not litellm.success_callback:
                    if self._original_callbacks:
                        litellm.success_callback = self._original_callbacks
                    else:
                        delattr(litellm, 'success_callback')
            
            # Restore original completion function if we modified it
            if self._original_completion_function is not None:
                litellm.completion = self._original_completion_function
                self._original_completion_function = None
            
            self._callback_registered = False
            logger.info("LiteLLM auto-integration teardown successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to teardown LiteLLM auto-integration: {e}")
            return False
    
    def is_auto_integration_active(self) -> bool:
        """Check if LiteLLM auto-integration is active."""
        return self._callback_registered
    
    def _litellm_success_callback(self, kwargs, response, start_time, end_time):
        """LiteLLM success callback that records conversations."""
        try:
            if not self.memori_instance or not self.memori_instance.is_enabled:
                return
            
            # Use pattern manager for consistent response handling
            self.memori_instance.pattern_manager.handle_response(
                ProviderType.LITELLM, PatternType.AUTO_INTEGRATION, response, kwargs
            )
            
        except Exception as e:
            logger.error(f"LiteLLM callback failed: {e}")
    
    def _setup_context_injection(self):
        """Set up context injection by wrapping LiteLLM's completion function."""
        try:
            if self._original_completion_function is not None:
                # Already set up
                return
            
            # Store original completion function
            self._original_completion_function = litellm.completion
            
            # Create wrapper function that injects context
            provider_self = self
            
            def completion_with_context(*args, **kwargs):
                # Use pattern manager for consistent request handling
                kwargs = provider_self.memori_instance.pattern_manager.handle_request(
                    ProviderType.LITELLM, PatternType.AUTO_INTEGRATION, kwargs
                )
                # Call original completion function
                return provider_self._original_completion_function(*args, **kwargs)
            
            # Replace LiteLLM's completion function
            litellm.completion = completion_with_context
            
            logger.debug("LiteLLM context injection wrapper set up")
            
        except Exception as e:
            logger.error(f"Failed to set up LiteLLM context injection: {e}")
    
    # ========================
    # Wrapper Pattern (Best Practice)
    # ========================
    
    def create_wrapped_client(self, **kwargs) -> Any:
        """Create a wrapped LiteLLM client."""
        if not LITELLM_AVAILABLE:
            raise ImportError("LiteLLM package not available")
        
        try:
            return MemoriLiteLLMClient(self, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create wrapped LiteLLM client: {e}")
            raise
    
    # ========================
    # Manual Recording Pattern (Manual Utility)
    # ========================
    
    def parse_manual_response(self, response: Any, user_input: str = "", **kwargs) -> ProviderResponse:
        """Parse LiteLLM response for manual recording."""
        try:
            # Extract content from response
            content = ""
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    content = choice.message.content or ""
                elif hasattr(choice, "text"):
                    content = choice.text or ""
            
            # Extract model
            model = kwargs.get("model", "litellm-unknown")
            if hasattr(response, "model"):
                model = response.model
            
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
                provider_type=ProviderType.LITELLM,
                pattern_type=PatternType.MANUAL_RECORDING,
                metadata=metadata,
                original_response=response,
                tokens_used=tokens_used,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse LiteLLM manual response: {e}")
            # Return minimal response to avoid breaking caller
            return ProviderResponse(
                content="[Error parsing response]",
                model="litellm-unknown",
                provider_type=ProviderType.LITELLM,
                pattern_type=PatternType.MANUAL_RECORDING,
                metadata={"error": str(e), "user_input": user_input, **kwargs},
                original_response=response,
                tokens_used=0,
            )
    
    # ========================
    # Common Provider Methods
    # ========================
    
    def inject_context(self, request: ProviderRequest) -> ProviderRequest:
        """LiteLLM-specific context injection (if needed)."""
        # The base UniversalContextInjector handles most cases
        # This method can be used for LiteLLM-specific customizations
        return request
    
    def extract_user_input(self, request_data: Dict[str, Any]) -> str:
        """Extract user input from LiteLLM request data."""
        try:
            messages = request_data.get("messages", [])
            # Find the last user message
            for message in reversed(messages):
                if message.get("role") == "user":
                    content = message.get("content", "")
                    return str(content)  # LiteLLM usually has simple string content
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extracting LiteLLM user input: {e}")
            return ""
    
    def parse_response(self, response: Any, request_data: Dict[str, Any]) -> ProviderResponse:
        """Parse LiteLLM response into standardized format."""
        try:
            # Extract content
            content = ""
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    content = choice.message.content or ""
                elif hasattr(choice, "text"):
                    content = choice.text or ""
            
            # Extract model
            model = request_data.get("model", "litellm-unknown")
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
                provider_type=ProviderType.LITELLM,
                pattern_type=PatternType.AUTO_INTEGRATION,  # Will be overridden by caller
                metadata=metadata,
                original_response=response,
                tokens_used=tokens_used,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse LiteLLM response: {e}")
            # Return minimal response to avoid breaking caller
            return ProviderResponse(
                content="[Error parsing response]",
                model="litellm-unknown",
                provider_type=ProviderType.LITELLM,
                pattern_type=PatternType.AUTO_INTEGRATION,
                metadata={"error": str(e), "original_request": request_data},
                original_response=response,
                tokens_used=0,
            )


class MemoriLiteLLMClient:
    """
    Wrapped LiteLLM client for the Wrapper Pattern (Best Practice).
    
    This provides a clean interface to LiteLLM's completion function
    that automatically records conversations through the unified architecture.
    """
    
    def __init__(self, provider: LiteLLMProvider, **kwargs):
        """Initialize wrapped LiteLLM client."""
        self.provider = provider
        self.memori_instance = provider.memori_instance
        self.config = kwargs
    
    def completion(self, **kwargs):
        """Wrapped completion function that automatically records conversations."""
        try:
            # Merge client config with call-specific kwargs
            merged_kwargs = {**self.config, **kwargs}
            
            # Use pattern manager for consistent request handling
            merged_kwargs = self.provider.memori_instance.pattern_manager.handle_request(
                ProviderType.LITELLM, PatternType.WRAPPER, merged_kwargs
            )
            
            # Make the actual API call
            response = litellm.completion(**merged_kwargs)
            
            # Use pattern manager for consistent response handling
            if self.provider.memori_instance.is_enabled:
                self.provider.memori_instance.pattern_manager.handle_response(
                    ProviderType.LITELLM, PatternType.WRAPPER, response, merged_kwargs
                )
            
            return response
            
        except Exception as e:
            logger.error(f"LiteLLM wrapper failed: {e}")
            raise
    
    def chat_completion(self, **kwargs):
        """Alias for completion function for compatibility."""
        return self.completion(**kwargs)
    
    def text_completion(self, **kwargs):
        """Text completion wrapper for legacy models."""
        return self.completion(**kwargs)