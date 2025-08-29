"""
MemoryManager - Modular memory management system for Memori

This is a working implementation that coordinates interceptors and provides
a clean interface for memory management operations.
"""

import uuid
from typing import Any, Dict, List, Optional

from loguru import logger

# Import interceptor managers
try:
    from ..integrations.openai_interceptor import setup_openai_interceptor
    OPENAI_INTERCEPTOR_AVAILABLE = True
except ImportError:
    OPENAI_INTERCEPTOR_AVAILABLE = False
    logger.warning("OpenAI interceptor not available")

try:
    from ..integrations.anthropic_interceptor import setup_anthropic_interceptor
    ANTHROPIC_INTERCEPTOR_AVAILABLE = True
except ImportError:
    ANTHROPIC_INTERCEPTOR_AVAILABLE = False
    logger.warning("Anthropic interceptor not available")


class MemoryManager:
    """
    Modular memory management system that coordinates interceptors,
    memory processing, and context injection.

    This class provides a clean interface for memory operations while
    maintaining backward compatibility with the existing Memori system.
    """

    def __init__(
        self,
        database_connect: str = "sqlite:///memori.db",
        template: str = "basic",
        mem_prompt: Optional[str] = None,
        conscious_ingest: bool = False,
        auto_ingest: bool = False,
        namespace: Optional[str] = None,
        shared_memory: bool = False,
        memory_filters: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        verbose: bool = False,
        provider_config: Optional[Any] = None,
        # Additional parameters for compatibility
        openai_api_key: Optional[str] = None,
        api_key: Optional[str] = None,
        api_type: Optional[str] = None,
        base_url: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        azure_ad_token: Optional[str] = None,
        organization: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the MemoryManager.

        Args:
            database_connect: Database connection string
            template: Memory template to use
            mem_prompt: Optional memory prompt
            conscious_ingest: Enable conscious memory ingestion
            auto_ingest: Enable automatic memory ingestion
            namespace: Optional namespace for memory isolation
            shared_memory: Enable shared memory across agents
            memory_filters: Optional memory filters
            user_id: Optional user identifier
            verbose: Enable verbose logging
            provider_config: Provider configuration
            **kwargs: Additional parameters for forward compatibility
        """
        self.database_connect = database_connect
        self.template = template
        self.mem_prompt = mem_prompt
        self.conscious_ingest = conscious_ingest
        self.auto_ingest = auto_ingest
        self.namespace = namespace
        self.shared_memory = shared_memory
        self.memory_filters = memory_filters or []
        self.user_id = user_id
        self.verbose = verbose
        self.provider_config = provider_config

        # Store additional configuration
        self.openai_api_key = openai_api_key
        self.api_key = api_key
        self.api_type = api_type
        self.base_url = base_url
        self.azure_endpoint = azure_endpoint
        self.azure_deployment = azure_deployment
        self.api_version = api_version
        self.azure_ad_token = azure_ad_token
        self.organization = organization
        self.kwargs = kwargs

        self._session_id = str(uuid.uuid4())
        self._enabled = False

        # LiteLLM native callback manager
        self.litellm_callback_manager = None
        
        # OpenAI and Anthropic interceptor managers
        self.openai_interceptor_manager = None
        self.anthropic_interceptor_manager = None

        logger.info(f"MemoryManager initialized with session: {self._session_id}")

    def set_memori_instance(self, memori_instance):
        """Set the parent Memori instance for memory management."""
        self.memori_instance = memori_instance
        
        # Initialize LiteLLM callback manager
        try:
            from ..integrations.litellm_integration import setup_litellm_callbacks
            self.litellm_callback_manager = setup_litellm_callbacks(memori_instance)
            if self.litellm_callback_manager:
                logger.debug("LiteLLM callback manager initialized")
            else:
                logger.warning("Failed to initialize LiteLLM callback manager")
        except ImportError as e:
            logger.warning(f"Could not initialize LiteLLM callback manager: {e}")
            
        # Initialize OpenAI interceptor manager
        if OPENAI_INTERCEPTOR_AVAILABLE:
            try:
                self.openai_interceptor_manager = setup_openai_interceptor(memori_instance)
                if self.openai_interceptor_manager:
                    logger.debug("OpenAI interceptor manager initialized")
                else:
                    logger.warning("Failed to initialize OpenAI interceptor manager")
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI interceptor manager: {e}")
        
        # Initialize Anthropic interceptor manager
        if ANTHROPIC_INTERCEPTOR_AVAILABLE:
            try:
                self.anthropic_interceptor_manager = setup_anthropic_interceptor(memori_instance)
                if self.anthropic_interceptor_manager:
                    logger.debug("Anthropic interceptor manager initialized")
                else:
                    logger.warning("Failed to initialize Anthropic interceptor manager")
            except Exception as e:
                logger.warning(f"Could not initialize Anthropic interceptor manager: {e}")
            
        logger.debug("MemoryManager configured with Memori instance")

    def enable(self, interceptors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Enable memory recording using LiteLLM native callbacks.

        Args:
            interceptors: Legacy parameter (ignored, using LiteLLM callbacks)

        Returns:
            Dict containing enablement results
        """
        if self._enabled:
            return {
                "success": True,
                "message": "Already enabled",
                "enabled_interceptors": ["litellm_native"],
            }

        if interceptors is None:
            interceptors = ["litellm_native", "openai_native", "anthropic_native"]

        try:
            enabled_interceptors = []
            
            # Enable LiteLLM native callback system
            if "litellm_native" in interceptors:
                if self.litellm_callback_manager and not self.litellm_callback_manager.is_registered:
                    success = self.litellm_callback_manager.register_callbacks()
                    if success:
                        enabled_interceptors.append("litellm_native")
                    else:
                        logger.warning("Failed to register LiteLLM callbacks")
                elif not self.litellm_callback_manager:
                    logger.warning("No LiteLLM callback manager available")
            
            # Enable OpenAI interceptor
            if "openai_native" in interceptors:
                if self.openai_interceptor_manager and not self.openai_interceptor_manager.is_registered:
                    success = self.openai_interceptor_manager.register_interceptor()
                    if success:
                        enabled_interceptors.append("openai_native")
                    else:
                        logger.warning("Failed to register OpenAI interceptor")
                elif not self.openai_interceptor_manager:
                    logger.warning("No OpenAI interceptor manager available")
            
            # Enable Anthropic interceptor
            if "anthropic_native" in interceptors:
                if self.anthropic_interceptor_manager and not self.anthropic_interceptor_manager.is_registered:
                    success = self.anthropic_interceptor_manager.register_interceptor()
                    if success:
                        enabled_interceptors.append("anthropic_native")
                    else:
                        logger.warning("Failed to register Anthropic interceptor")
                elif not self.anthropic_interceptor_manager:
                    logger.warning("No Anthropic interceptor manager available")
            
            if enabled_interceptors:
                self._enabled = True
                logger.info(f"MemoryManager enabled with interceptors: {', '.join(enabled_interceptors)}")
                return {
                    "success": True,
                    "message": f"Enabled interceptors: {', '.join(enabled_interceptors)}",
                    "enabled_interceptors": enabled_interceptors,
                }
            else:
                logger.warning("No interceptors were successfully enabled")
                return {
                    "success": False,
                    "message": "No interceptors were successfully enabled"
                }
                
        except Exception as e:
            logger.error(f"Failed to enable MemoryManager: {e}")
            return {"success": False, "message": str(e)}

    def disable(self) -> Dict[str, Any]:
        """
        Disable memory recording using LiteLLM native callbacks.

        Returns:
            Dict containing disable results
        """
        if not self._enabled:
            return {"success": True, "message": "Already disabled"}

        try:
            disabled_interceptors = []
            
            # Disable LiteLLM native callback system
            if self.litellm_callback_manager and self.litellm_callback_manager.is_registered:
                success = self.litellm_callback_manager.unregister_callbacks()
                if success:
                    disabled_interceptors.append("litellm_native")
                else:
                    logger.warning("Failed to unregister LiteLLM callbacks")
            
            # Disable OpenAI interceptor
            if self.openai_interceptor_manager and self.openai_interceptor_manager.is_registered:
                success = self.openai_interceptor_manager.unregister_interceptor()
                if success:
                    disabled_interceptors.append("openai_native")
                else:
                    logger.warning("Failed to unregister OpenAI interceptor")
            
            # Disable Anthropic interceptor
            if self.anthropic_interceptor_manager and self.anthropic_interceptor_manager.is_registered:
                success = self.anthropic_interceptor_manager.unregister_interceptor()
                if success:
                    disabled_interceptors.append("anthropic_native")
                else:
                    logger.warning("Failed to unregister Anthropic interceptor")
            
            self._enabled = False

            logger.info(f"MemoryManager disabled: {', '.join(disabled_interceptors) if disabled_interceptors else 'No interceptors were active'}")

            return {
                "success": True,
                "message": f"MemoryManager disabled successfully. Disabled interceptors: {', '.join(disabled_interceptors) if disabled_interceptors else 'None'}",
                "disabled_interceptors": disabled_interceptors,
            }
        except Exception as e:
            logger.error(f"Failed to disable MemoryManager: {e}")
            return {"success": False, "message": str(e)}

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of memory recording system.

        Returns:
            Dict containing memory system status information
        """
        status = {}
        
        # LiteLLM status
        litellm_status = "inactive"
        if self.litellm_callback_manager:
            if self.litellm_callback_manager.is_registered:
                litellm_status = "active"
            else:
                litellm_status = "available_but_not_registered"
        else:
            litellm_status = "unavailable"
            
        status["litellm_native"] = {
            "enabled": self.litellm_callback_manager.is_registered if self.litellm_callback_manager else False,
            "status": litellm_status,
            "method": "litellm_callbacks",
            "session_id": self._session_id,
            "callback_manager": self.litellm_callback_manager is not None,
        }
        
        # OpenAI status
        openai_status = "inactive"
        if self.openai_interceptor_manager:
            if self.openai_interceptor_manager.is_registered:
                openai_status = "active"
            else:
                openai_status = "available_but_not_registered"
        else:
            openai_status = "unavailable"
            
        status["openai_native"] = {
            "enabled": self.openai_interceptor_manager.is_registered if self.openai_interceptor_manager else False,
            "status": openai_status,
            "method": "openai_interceptor",
            "session_id": self._session_id,
            "interceptor_manager": self.openai_interceptor_manager is not None,
        }
        
        # Anthropic status
        anthropic_status = "inactive"
        if self.anthropic_interceptor_manager:
            if self.anthropic_interceptor_manager.is_registered:
                anthropic_status = "active"
            else:
                anthropic_status = "available_but_not_registered"
        else:
            anthropic_status = "unavailable"
            
        status["anthropic_native"] = {
            "enabled": self.anthropic_interceptor_manager.is_registered if self.anthropic_interceptor_manager else False,
            "status": anthropic_status,
            "method": "anthropic_interceptor",
            "session_id": self._session_id,
            "interceptor_manager": self.anthropic_interceptor_manager is not None,
        }
            
        return status

    def get_health(self) -> Dict[str, Any]:
        """
        Get health check of the memory management system.

        Returns:
            Dict containing health information
        """
        return {
            "session_id": self._session_id,
            "enabled": self._enabled,
            "namespace": self.namespace,
            "user_id": self.user_id,
            "litellm_callback_manager": self.litellm_callback_manager is not None,
            "litellm_callbacks_registered": self.litellm_callback_manager.is_registered if self.litellm_callback_manager else False,
            "openai_interceptor_manager": self.openai_interceptor_manager is not None,
            "openai_interceptor_registered": self.openai_interceptor_manager.is_registered if self.openai_interceptor_manager else False,
            "anthropic_interceptor_manager": self.anthropic_interceptor_manager is not None,
            "anthropic_interceptor_registered": self.anthropic_interceptor_manager.is_registered if self.anthropic_interceptor_manager else False,
            "memory_filters": len(self.memory_filters),
            "conscious_ingest": self.conscious_ingest,
            "auto_ingest": self.auto_ingest,
            "database_connect": self.database_connect,
            "template": self.template,
        }

    # === BACKWARD COMPATIBILITY PROPERTIES ===

    @property
    def session_id(self) -> str:
        """Get session ID for backward compatibility."""
        return self._session_id

    @property
    def enabled(self) -> bool:
        """Check if enabled for backward compatibility."""
        return self._enabled

    # === PLACEHOLDER METHODS FOR FUTURE MODULAR COMPONENTS ===

    def record_conversation(
        self,
        user_input: str,
        ai_output: str,
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record a conversation (placeholder for future implementation).

        Returns:
            Placeholder conversation ID
        """
        logger.info(f"Recording conversation (placeholder): {user_input[:50]}...")
        return str(uuid.uuid4())

    def search_memories(
        self,
        query: str,
        limit: int = 5,
        memory_types: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        min_importance: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search memories (placeholder for future implementation).

        Returns:
            Empty list (placeholder)
        """
        logger.info(f"Searching memories (placeholder): {query}")
        return []

    def cleanup(self):
        """Cleanup resources."""
        try:
            if self._enabled:
                self.disable()
            
            # Clean up callback manager
            if self.litellm_callback_manager:
                self.litellm_callback_manager.unregister_callbacks()
                self.litellm_callback_manager = None
            
            # Clean up OpenAI interceptor
            if self.openai_interceptor_manager:
                self.openai_interceptor_manager.unregister_interceptor()
                self.openai_interceptor_manager = None
                
            # Clean up Anthropic interceptor
            if self.anthropic_interceptor_manager:
                self.anthropic_interceptor_manager.unregister_interceptor()
                self.anthropic_interceptor_manager = None
                
            logger.info("MemoryManager cleanup completed")
        except Exception as e:
            logger.error(f"Error during MemoryManager cleanup: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

    def __del__(self):
        """Destructor - ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass