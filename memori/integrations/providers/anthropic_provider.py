"""
Anthropic Provider Implementation for Unified Three-Tier Architecture

This module implements the unified three-tier architecture for Anthropic:
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
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic package not available")


class AnthropicProvider(BaseProvider):
    """
    Anthropic provider implementation for the unified three-tier architecture.
    
    Supports all three patterns:
    - Auto-Integration: Monkey-patches Anthropic SDK methods
    - Wrapper: Provides clean MemoriAnthropic client
    - Manual Recording: Parses Anthropic responses for manual recording
    """
    
    def __init__(self, memori_instance, provider_type: ProviderType, **kwargs):
        """Initialize Anthropic provider."""
        super().__init__(memori_instance, provider_type, **kwargs)
        self._original_create_method = None
        self._auto_integration_active = False
        
    def _check_availability(self) -> bool:
        """Check if Anthropic is available."""
        return ANTHROPIC_AVAILABLE
    
    # ========================
    # Auto-Integration Pattern (Magic)
    # ========================
    
    def setup_auto_integration(self) -> bool:
        """Set up Anthropic auto-integration by monkey-patching SDK methods."""
        if not ANTHROPIC_AVAILABLE:
            logger.error("Anthropic not available - cannot setup auto-integration")
            return False
            
        if self._auto_integration_active:
            logger.warning("Anthropic auto-integration already active")
            return True
        
        try:
            from anthropic.resources.messages import Messages
            
            # Store original method
            self._original_create_method = Messages.create
            
            # Create intercepted method with closure to capture self
            provider_self = self
            
            def intercepted_create(messages_self, **kwargs):
                try:
                    # Use the pattern manager for consistent request handling
                    kwargs = provider_self.memori_instance.pattern_manager.handle_request(
                        ProviderType.ANTHROPIC, PatternType.AUTO_INTEGRATION, kwargs
                    )
                    
                    # Call original method
                    response = provider_self._original_create_method(messages_self, **kwargs)
                    
                    # Use pattern manager for consistent response handling
                    if provider_self.memori_instance.is_enabled:
                        provider_self.memori_instance.pattern_manager.handle_response(
                            ProviderType.ANTHROPIC, PatternType.AUTO_INTEGRATION, response, kwargs
                        )
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"Anthropic auto-integration failed: {e}")
                    # Fallback to original method
                    return provider_self._original_create_method(messages_self, **kwargs)
            
            # Replace the method
            Messages.create = intercepted_create
            
            self._auto_integration_active = True
            logger.info("Anthropic auto-integration setup successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Anthropic auto-integration: {e}")
            return False
    
    def teardown_auto_integration(self) -> bool:
        """Tear down Anthropic auto-integration."""
        if not ANTHROPIC_AVAILABLE:
            return False
            
        if not self._auto_integration_active:
            return True
        
        try:
            from anthropic.resources.messages import Messages
            
            # Restore original method
            if self._original_create_method is not None:
                Messages.create = self._original_create_method
                self._original_create_method = None
            
            self._auto_integration_active = False
            logger.info("Anthropic auto-integration teardown successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to teardown Anthropic auto-integration: {e}")
            return False
    
    def is_auto_integration_active(self) -> bool:
        """Check if Anthropic auto-integration is active."""
        return self._auto_integration_active
    
    # ========================
    # Wrapper Pattern (Best Practice)
    # ========================
    
    def create_wrapped_client(self, **kwargs) -> Any:
        """Create a wrapped Anthropic client."""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package not available")
        
        try:
            return MemoriAnthropicClient(self, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create wrapped Anthropic client: {e}")
            raise
    
    # ========================
    # Manual Recording Pattern (Manual Utility)
    # ========================
    
    def parse_manual_response(self, response: Any, user_input: str = "", **kwargs) -> ProviderResponse:
        """Parse Anthropic response for manual recording."""
        try:
            # Extract content from response
            content = ""
            if hasattr(response, "content") and response.content:
                if isinstance(response.content, list):
                    # Handle structured content (text blocks, tool use, etc.)
                    text_parts = []
                    tool_uses = []
                    
                    for block in response.content:
                        try:
                            # Handle text blocks
                            if hasattr(block, "text") and block.text:
                                text_parts.append(block.text)
                            # Handle tool use blocks
                            elif hasattr(block, "type"):
                                block_type = getattr(block, "type", None)
                                if block_type == "tool_use":
                                    tool_name = getattr(block, "name", "unknown")
                                    tool_input = getattr(block, "input", {})
                                    tool_uses.append(f"Used {tool_name} with {tool_input}")
                            # Handle mock objects for testing
                            elif hasattr(block, "name") and hasattr(block, "input"):
                                tool_name = getattr(block, "name", "unknown")
                                tool_input = getattr(block, "input", {})
                                tool_uses.append(f"Used {tool_name} with {tool_input}")
                        except Exception as block_error:
                            logger.debug(f"Error processing block: {block_error}")
                            continue
                    
                    content = " ".join(text_parts)
                    if tool_uses:
                        if content:
                            content += " "
                        content += "[Tool uses: " + "; ".join(tool_uses) + "]"
                        
                elif isinstance(response.content, str):
                    content = response.content
                else:
                    content = str(response.content)
            
            # Extract model
            model = getattr(response, "model", kwargs.get("model", "claude-unknown"))
            
            # Extract token usage
            tokens_used = 0
            if hasattr(response, "usage") and response.usage:
                input_tokens = getattr(response.usage, "input_tokens", 0)
                output_tokens = getattr(response.usage, "output_tokens", 0)
                tokens_used = input_tokens + output_tokens
            
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
                    "input_tokens": getattr(usage, "input_tokens", 0),
                    "output_tokens": getattr(usage, "output_tokens", 0),
                })
            
            return ProviderResponse(
                content=content,
                model=model,
                provider_type=ProviderType.ANTHROPIC,
                pattern_type=PatternType.MANUAL_RECORDING,
                metadata=metadata,
                original_response=response,
                tokens_used=tokens_used,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Anthropic manual response: {e}")
            # Return minimal response to avoid breaking caller
            return ProviderResponse(
                content="[Error parsing response]",
                model="claude-unknown",
                provider_type=ProviderType.ANTHROPIC,
                pattern_type=PatternType.MANUAL_RECORDING,
                metadata={"error": str(e), "user_input": user_input, **kwargs},
                original_response=response,
                tokens_used=0,
            )
    
    # ========================
    # Common Provider Methods
    # ========================
    
    def inject_context(self, request: ProviderRequest) -> ProviderRequest:
        """Anthropic-specific context injection."""
        # Anthropic uses a "system" parameter instead of system messages
        if request.system_prompt:
            # Update the system parameter with context
            request.original_kwargs = request.original_kwargs.copy()
            if request.original_kwargs.get("system"):
                request.original_kwargs["system"] = request.system_prompt + request.original_kwargs["system"]
            else:
                request.original_kwargs["system"] = request.system_prompt
        
        return request
    
    def extract_user_input(self, request_data: Dict[str, Any]) -> str:
        """Extract user input from Anthropic request data."""
        try:
            messages = request_data.get("messages", [])
            # Find the last user message
            for message in reversed(messages):
                if message.get("role") == "user":
                    content = message.get("content", "")
                    
                    if isinstance(content, str):
                        return content
                    elif isinstance(content, list):
                        # Handle content blocks
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                        return " ".join(text_parts)
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error extracting Anthropic user input: {e}")
            return ""
    
    def parse_response(self, response: Any, request_data: Dict[str, Any]) -> ProviderResponse:
        """Parse Anthropic response into standardized format."""
        try:
            # Extract content
            content = ""
            if hasattr(response, "content") and response.content:
                if isinstance(response.content, list):
                    # Handle structured content (text blocks, tool use, etc.)
                    text_parts = []
                    tool_uses = []
                    
                    for block in response.content:
                        try:
                            # Handle text blocks
                            if hasattr(block, "text") and block.text:
                                text_parts.append(block.text)
                            # Handle tool use blocks
                            elif hasattr(block, "type"):
                                block_type = getattr(block, "type", None)
                                if block_type == "tool_use":
                                    tool_name = getattr(block, "name", "unknown")
                                    tool_input = getattr(block, "input", {})
                                    tool_uses.append(f"Used {tool_name} with {tool_input}")
                            # Handle mock objects for testing
                            elif hasattr(block, "name") and hasattr(block, "input"):
                                tool_name = getattr(block, "name", "unknown")
                                tool_input = getattr(block, "input", {})
                                tool_uses.append(f"Used {tool_name} with {tool_input}")
                        except Exception as block_error:
                            logger.debug(f"Error processing block: {block_error}")
                            continue
                    
                    content = " ".join(text_parts)
                    if tool_uses:
                        if content:
                            content += " "
                        content += "[Tool uses: " + "; ".join(tool_uses) + "]"
                        
                elif isinstance(response.content, str):
                    content = response.content
                else:
                    content = str(response.content)
            
            # Extract model
            model = request_data.get("model", "claude-unknown")
            if hasattr(response, "model"):
                model = response.model
            
            # Extract token usage
            tokens_used = 0
            if hasattr(response, "usage") and response.usage:
                input_tokens = getattr(response.usage, "input_tokens", 0)
                output_tokens = getattr(response.usage, "output_tokens", 0)
                tokens_used = input_tokens + output_tokens
            
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
            if hasattr(response, "stop_reason"):
                metadata["stop_reason"] = response.stop_reason
            if hasattr(response, "model"):
                metadata["response_model"] = response.model
            
            # Add detailed token usage
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                metadata.update({
                    "input_tokens": getattr(usage, "input_tokens", 0),
                    "output_tokens": getattr(usage, "output_tokens", 0),
                })
            
            return ProviderResponse(
                content=content,
                model=model,
                provider_type=ProviderType.ANTHROPIC,
                pattern_type=PatternType.AUTO_INTEGRATION,  # Will be overridden by caller
                metadata=metadata,
                original_response=response,
                tokens_used=tokens_used,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Anthropic response: {e}")
            # Return minimal response to avoid breaking caller
            return ProviderResponse(
                content="[Error parsing response]",
                model="claude-unknown",
                provider_type=ProviderType.ANTHROPIC,
                pattern_type=PatternType.AUTO_INTEGRATION,
                metadata={"error": str(e), "original_request": request_data},
                original_response=response,
                tokens_used=0,
            )


class MemoriAnthropicClient:
    """
    Wrapped Anthropic client for the Wrapper Pattern (Best Practice).
    
    This provides a clean, drop-in replacement for the Anthropic client
    that automatically records conversations through the unified architecture.
    """
    
    def __init__(self, provider: AnthropicProvider, **kwargs):
        """Initialize wrapped Anthropic client."""
        self.provider = provider
        self.memori_instance = provider.memori_instance
        
        # Create actual Anthropic client
        self._client = anthropic.Anthropic(**kwargs)
        
        # Create wrapped interfaces
        self.messages = self._create_messages_wrapper()
        
        # Pass through other attributes
        for attr in dir(self._client):
            if not attr.startswith("_") and attr not in ["messages"]:
                setattr(self, attr, getattr(self._client, attr))
    
    def _create_messages_wrapper(self):
        """Create wrapped messages interface."""
        
        class MessagesWrapper:
            def __init__(self, client, provider):
                self._client = client
                self.provider = provider
            
            def create(self, **kwargs):
                try:
                    # Use pattern manager for consistent request handling
                    kwargs = self.provider.memori_instance.pattern_manager.handle_request(
                        ProviderType.ANTHROPIC, PatternType.WRAPPER, kwargs
                    )
                    
                    # Make the actual API call
                    response = self._client.messages.create(**kwargs)
                    
                    # Use pattern manager for consistent response handling
                    if self.provider.memori_instance.is_enabled:
                        self.provider.memori_instance.pattern_manager.handle_response(
                            ProviderType.ANTHROPIC, PatternType.WRAPPER, response, kwargs
                        )
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"Anthropic wrapper failed: {e}")
                    raise
        
        return MessagesWrapper(self._client, self.provider)