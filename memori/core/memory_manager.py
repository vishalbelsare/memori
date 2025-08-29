"""
MemoryManager - Modular memory management system for Memori

This is a working implementation that coordinates interceptors and provides
a clean interface for memory management operations.
"""

import uuid
from typing import Any, Dict, List, Optional

from loguru import logger

from ..interceptors import InterceptorManager


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

        # Initialize interceptor manager - this will be passed the parent Memori instance
        self.interceptor_manager = None

        logger.info(f"MemoryManager initialized with session: {self._session_id}")

    def set_memori_instance(self, memori_instance):
        """Set the parent Memori instance for interceptor management."""
        self.interceptor_manager = InterceptorManager(memori_instance)
        logger.debug("InterceptorManager initialized")

    def enable(self, interceptors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Enable memory recording interceptors.

        Args:
            interceptors: List of interceptor types to enable

        Returns:
            Dict containing enablement results
        """
        if self._enabled:
            return {
                "success": True,
                "message": "Already enabled",
                "enabled_interceptors": [],
            }

        if interceptors is None:
            interceptors = ["native", "openai", "anthropic", "http"]

        if self.interceptor_manager is None:
            logger.warning(
                "InterceptorManager not initialized - cannot enable interceptors"
            )
            return {"success": False, "message": "InterceptorManager not initialized"}

        try:
            results = self.interceptor_manager.enable(interceptors)
            self._enabled = True

            logger.info(f"MemoryManager enabled with interceptors: {interceptors}")
            enabled_count = sum(1 for success in results.values() if success)
            enabled_interceptors = [
                name for name, success in results.items() if success
            ]

            return {
                "success": True,
                "message": f"Enabled {enabled_count} interceptors",
                "enabled_interceptors": enabled_interceptors,
            }
        except Exception as e:
            logger.error(f"Failed to enable MemoryManager: {e}")
            return {"success": False, "message": str(e)}

    def disable(self) -> Dict[str, Any]:
        """
        Disable memory recording interceptors.

        Returns:
            Dict containing disable results
        """
        if not self._enabled:
            return {"success": True, "message": "Already disabled"}

        if self.interceptor_manager is None:
            logger.warning("InterceptorManager not initialized")
            return {"success": False, "message": "InterceptorManager not initialized"}

        try:
            results = self.interceptor_manager.disable()
            self._enabled = False

            logger.info("MemoryManager disabled")
            disabled_count = sum(1 for success in results.values() if success)

            return {
                "success": True,
                "message": f"MemoryManager disabled successfully ({disabled_count} interceptors)",
            }
        except Exception as e:
            logger.error(f"Failed to disable MemoryManager: {e}")
            return {"success": False, "message": str(e)}

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all interceptors.

        Returns:
            Dict containing interceptor status information
        """
        if self.interceptor_manager is None:
            return {}

        try:
            return self.interceptor_manager.get_status()
        except Exception as e:
            logger.error(f"Failed to get interceptor status: {e}")
            return {}

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
            "interceptor_manager": self.interceptor_manager is not None,
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
