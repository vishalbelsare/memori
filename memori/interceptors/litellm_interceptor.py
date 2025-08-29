"""
LiteLLM native callback interceptor for clean conversation recording.
"""

from typing import Any, Dict, TYPE_CHECKING

from loguru import logger

from .base import ConversationInterceptor

if TYPE_CHECKING:
    from ..core.memory import Memori


class LiteLLMNativeInterceptor(ConversationInterceptor):
    """Native LiteLLM callback interceptor - cleanest approach"""
    
    def __init__(self, memori_instance: 'Memori'):
        super().__init__(memori_instance)
        self._callback_registered = False
        self._original_completion = None
        
    def enable(self) -> bool:
        """Enable LiteLLM native callbacks"""
        with self._lock:
            if self._enabled:
                return True
                
            try:
                import litellm
                from litellm import success_callback
                
                # Register success callback
                if self._litellm_success_callback not in success_callback:
                    success_callback.append(self._litellm_success_callback)
                    self._callback_registered = True
                
                # Register context injection hook using LiteLLM's native callback system
                if hasattr(litellm, 'input_callback') and not hasattr(self, '_input_callback_registered'):
                    # Use native input callback for context injection
                    litellm.input_callback.append(self._litellm_input_callback)
                    self._input_callback_registered = True
                elif not hasattr(litellm.completion, "_memori_enhanced"):
                    # Fallback to minimal function wrapping only if input callbacks unavailable
                    self._original_completion = litellm.completion
                    
                    def enhanced_completion(*args, **kwargs):
                        # Inject context based on ingestion mode
                        if self.memori.is_enabled:
                            if self.memori.auto_ingest:
                                kwargs = self.memori._inject_litellm_context(kwargs, mode="auto")
                            elif self.memori.conscious_ingest:
                                kwargs = self.memori._inject_litellm_context(kwargs, mode="conscious")
                        
                        return self._original_completion(*args, **kwargs)
                    
                    litellm.completion = enhanced_completion
                    litellm.completion._memori_enhanced = True
                    logger.debug("LiteLLM: Using function wrapping (input callbacks not available)")
                else:
                    logger.debug("LiteLLM: Using native input callbacks")
                
                self._enabled = True
                logger.debug("LiteLLM native interceptor enabled")
                return True
                
            except ImportError:
                logger.debug("LiteLLM not available")
                return False
            except Exception as e:
                logger.error(f"Failed to enable LiteLLM interceptor: {e}")
                return False
    
    def disable(self) -> bool:
        """Disable LiteLLM native callbacks"""
        with self._lock:
            if not self._enabled:
                return True
                
            try:
                import litellm
                from litellm import success_callback
                
                # Remove success callback
                if self._callback_registered and self._litellm_success_callback in success_callback:
                    success_callback.remove(self._litellm_success_callback)
                    self._callback_registered = False
                
                # Remove input callback if registered
                if hasattr(self, '_input_callback_registered') and hasattr(litellm, 'input_callback'):
                    try:
                        litellm.input_callback.remove(self._litellm_input_callback)
                        delattr(self, '_input_callback_registered')
                    except ValueError:
                        pass  # Callback already removed
                
                # Restore original completion if wrapped
                if self._original_completion and hasattr(litellm.completion, '_memori_enhanced'):
                    litellm.completion = self._original_completion
                    self._original_completion = None
                
                self._enabled = False
                logger.debug("LiteLLM native interceptor disabled")
                return True
                
            except ImportError:
                logger.debug("LiteLLM not available")
                return True
            except Exception as e:
                logger.error(f"Failed to disable LiteLLM interceptor: {e}")
                return False
    
    def _litellm_input_callback(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Native LiteLLM input callback for context injection"""
        if not self._should_allow_operation():
            return kwargs
            
        try:
            if self.memori.is_enabled:
                if self.memori.auto_ingest:
                    kwargs = self.memori._inject_litellm_context(kwargs, mode="auto")
                elif self.memori.conscious_ingest:
                    kwargs = self.memori._inject_litellm_context(kwargs, mode="conscious")
                self._record_success()
        except Exception as e:
            logger.debug(f"LiteLLM input callback error: {e}")
            self._record_failure()
        
        return kwargs
    
    def _litellm_success_callback(self, kwargs: Dict[str, Any], response: Any, start_time: float, end_time: float):
        """Native LiteLLM success callback for recording conversations"""
        if not self._should_allow_operation():
            return
            
        try:
            self.memori._process_litellm_response(kwargs, response, start_time, end_time)
            self._record_success()
        except Exception as e:
            logger.debug(f"LiteLLM success callback error: {e}")
            self._record_failure()