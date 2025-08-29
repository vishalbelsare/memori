"""
OpenAI Interceptor - Simple and Effective SDK Interception
"""

from typing import Any, Dict, Optional
from loguru import logger

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - native interception system disabled")


class OpenAIInterceptorManager:
    """
    Simple OpenAI SDK interceptor that monkey-patches the chat completions create method.
    """
    
    def __init__(self, memori_instance):
        self.memori_instance = memori_instance
        self._interceptor_registered = False
        self._original_create_method = None
        
    def register_interceptor(self) -> bool:
        """Register OpenAI SDK interception."""
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI not available - cannot register interceptor")
            return False
            
        if self._interceptor_registered:
            logger.warning("OpenAI interceptor already registered")
            return True
            
        try:
            # Import the actual modules we need to patch
            from openai.resources.chat.completions import Completions
            
            # Store the original create method
            self._original_create_method = Completions.create
            
            # Create the intercepted method
            def intercepted_create(self_completions, **kwargs):
                try:
                    # Inject context if needed
                    interceptor = self.memori_instance.memory_manager.openai_interceptor_manager
                    if (interceptor and interceptor.memori_instance.is_enabled and 
                        (interceptor.memori_instance.conscious_ingest or interceptor.memori_instance.auto_ingest)):
                        kwargs = interceptor.memori_instance._inject_openai_context(kwargs)
                    
                    # Call original method
                    response = interceptor._original_create_method(self_completions, **kwargs)
                    
                    # Record conversation if enabled
                    if (interceptor and interceptor.memori_instance.is_enabled):
                        interceptor.memori_instance._record_openai_conversation(kwargs, response)
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"OpenAI interception failed: {e}")
                    # Fallback to original method
                    original_method = self.memori_instance.memory_manager.openai_interceptor_manager._original_create_method
                    return original_method(self_completions, **kwargs)
            
            # Replace the method
            Completions.create = intercepted_create
            
            self._interceptor_registered = True
            logger.info("OpenAI SDK interceptor registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register OpenAI interceptor: {e}")
            return False
    
    def unregister_interceptor(self) -> bool:
        """Unregister OpenAI interceptor."""
        if not OPENAI_AVAILABLE:
            return False
            
        if not self._interceptor_registered:
            logger.warning("OpenAI interceptor not registered")
            return True
            
        try:
            from openai.resources.chat.completions import Completions
            
            # Restore original method
            if self._original_create_method is not None:
                Completions.create = self._original_create_method
                self._original_create_method = None
            
            self._interceptor_registered = False
            logger.info("OpenAI SDK interceptor unregistered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister OpenAI interceptor: {e}")
            return False
    
    @property
    def is_registered(self) -> bool:
        """Check if interceptor is registered."""
        return self._interceptor_registered


def setup_openai_interceptor(memori_instance) -> Optional[OpenAIInterceptorManager]:
    """
    Set up OpenAI interceptor for a Memori instance.
    """
    if not OPENAI_AVAILABLE:
        logger.error("OpenAI not available - cannot set up interceptor")
        return None
    
    interceptor_manager = OpenAIInterceptorManager(memori_instance)
    if interceptor_manager.register_interceptor():
        return interceptor_manager
    return None