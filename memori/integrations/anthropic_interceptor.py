"""
Anthropic Interceptor - Native SDK Interception
"""

from typing import Any, Dict, Optional
from loguru import logger

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic not available - native interception system disabled")


class AnthropicInterceptorManager:
    """
    Manages Anthropic SDK interception for automatic memory recording.
    
    This class monkey-patches the Anthropic SDK to automatically intercept
    API calls and record conversations into Memori.
    """
    
    def __init__(self, memori_instance):
        """
        Initialize Anthropic interceptor manager.
        
        Args:
            memori_instance: The Memori instance to record conversations to
        """
        self.memori_instance = memori_instance
        self._interceptor_registered = False
        self._original_messages_create = None
        
    def register_interceptor(self) -> bool:
        """
        Register Anthropic SDK interception for automatic memory recording.
        
        Returns:
            True if registration successful, False otherwise
        """
        if not ANTHROPIC_AVAILABLE:
            logger.error("Anthropic not available - cannot register interceptor")
            return False
            
        if self._interceptor_registered:
            logger.warning("Anthropic interceptor already registered")
            return True
            
        try:
            # Store original method
            self._original_messages_create = anthropic.Anthropic.messages.create
            
            # Monkey-patch messages create
            anthropic.Anthropic.messages.create = self._intercepted_messages_create
            
            self._interceptor_registered = True
            logger.info("Anthropic SDK interceptor registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register Anthropic interceptor: {e}")
            return False
    
    def unregister_interceptor(self) -> bool:
        """
        Unregister Anthropic interceptor and restore original method.
        
        Returns:
            True if unregistration successful, False otherwise
        """
        if not ANTHROPIC_AVAILABLE:
            return False
            
        if not self._interceptor_registered:
            logger.warning("Anthropic interceptor not registered")
            return True
            
        try:
            # Restore original method
            if self._original_messages_create is not None:
                anthropic.Anthropic.messages.create = self._original_messages_create
                self._original_messages_create = None
            
            self._interceptor_registered = False
            logger.info("Anthropic SDK interceptor unregistered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister Anthropic interceptor: {e}")
            return False
    
    def _intercepted_messages_create(self, **kwargs):
        """
        Intercepted messages create method that records conversations.
        
        This method wraps the original Anthropic messages API call.
        """
        try:
            # Inject context if conscious or auto ingestion is enabled
            if self.memori_instance.is_enabled and (self.memori_instance.conscious_ingest or self.memori_instance.auto_ingest):
                kwargs = self.memori_instance._inject_anthropic_context(kwargs)
            
            # Make the actual API call using the original method
            response = self._original_messages_create(**kwargs)
            
            # Record conversation if memori is enabled
            if self.memori_instance.is_enabled:
                self._record_messages_conversation(kwargs, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Anthropic messages interception failed: {e}")
            # Fallback to original method if interception fails
            return self._original_messages_create(**kwargs)
    
    def _record_messages_conversation(self, kwargs, response):
        """Record Anthropic messages conversation"""
        try:
            # Use the existing enhanced recording method from Memori
            self.memori_instance._record_anthropic_conversation(kwargs, response)
            logger.debug("Anthropic conversation recorded via interceptor")
            
        except Exception as e:
            logger.error(f"Failed to record Anthropic conversation via interceptor: {e}")
    
    @property
    def is_registered(self) -> bool:
        """Check if interceptor is registered."""
        return self._interceptor_registered


def setup_anthropic_interceptor(memori_instance) -> Optional[AnthropicInterceptorManager]:
    """
    Convenience function to set up Anthropic interceptor for a Memori instance.
    
    Args:
        memori_instance: The Memori instance to record conversations to
        
    Returns:
        AnthropicInterceptorManager instance if successful, None otherwise
    """
    if not ANTHROPIC_AVAILABLE:
        logger.error("Anthropic not available - cannot set up interceptor")
        return None
    
    interceptor_manager = AnthropicInterceptorManager(memori_instance)
    if interceptor_manager.register_interceptor():
        return interceptor_manager
    return None