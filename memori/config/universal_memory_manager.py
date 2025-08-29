"""
Universal Memory Manager - Three-Tier Architecture Manager

This class coordinates the unified three-tier architecture across all providers
using the UniversalPatternManager and provider registry system.

Replaces the original MemoryManager with a unified approach that works
consistently across OpenAI, Anthropic, LiteLLM, and any future providers.
"""

import uuid
from typing import Any, Dict, List, Optional

from loguru import logger

# Import unified architecture components
from ..core.pattern_manager import UniversalPatternManager
from ..core.providers_base import ProviderType
from ..integrations.providers import get_available_providers


class UniversalMemoryManager:
    """
    Universal memory management system that coordinates the three-tier architecture
    across all LLM providers.

    This class provides a unified interface for:
    1. Auto-Integration Pattern (Magic): Automatic interception
    2. Wrapper Pattern (Best Practice): Wrapped clients
    3. Manual Recording Pattern (Manual Utility): Manual recording

    It replaces the original MemoryManager with a provider-agnostic approach.
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
        Initialize the Universal Memory Manager.

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
        
        # Universal pattern manager (will be initialized when memori instance is set)
        self.pattern_manager = None

        logger.info(f"UniversalMemoryManager initialized with session: {self._session_id}")

    def set_memori_instance(self, memori_instance):
        """Set the parent Memori instance for memory management."""
        self.memori_instance = memori_instance
        
        # Initialize universal pattern manager
        try:
            self.pattern_manager = UniversalPatternManager(memori_instance)
            # Also set pattern_manager on memori instance for easy access
            memori_instance.pattern_manager = self.pattern_manager
            logger.info("Universal pattern manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize universal pattern manager: {e}")
            self.pattern_manager = None
            
        logger.debug("UniversalMemoryManager configured with Memori instance")

    def enable(self, interceptors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Enable memory recording using the universal three-tier architecture.

        Args:
            interceptors: List of interceptor types to enable (legacy parameter)
                         If None, enables all available providers for auto-integration

        Returns:
            Dict containing enablement results
        """
        if self._enabled:
            return {
                "success": True,
                "message": "Already enabled",
                "enabled_providers": self._get_enabled_providers(),
            }

        if not self.pattern_manager:
            logger.error("Pattern manager not initialized")
            return {"success": False, "message": "Pattern manager not available"}

        try:
            # Determine which providers to enable
            if interceptors is None:
                # Enable auto-integration for all available providers
                provider_types = get_available_providers()
            else:
                # Map legacy interceptor names to provider types
                provider_types = self._map_interceptors_to_providers(interceptors)
            
            # Enable auto-integration pattern for all specified providers
            results = self.pattern_manager.enable_auto_integration(provider_types)
            
            if results["success"]:
                self._enabled = True
                logger.info(f"Universal MemoryManager enabled for providers: {', '.join(results['enabled_providers'])}")
                return {
                    "success": True,
                    "message": results["message"],
                    "enabled_providers": results["enabled_providers"],
                    "enabled_interceptors": results["enabled_providers"],  # For backward compatibility
                    "session_id": self._session_id,
                }
            else:
                logger.warning(f"Failed to enable universal MemoryManager: {results['message']}")
                return {
                    "success": False,
                    "message": results["message"],
                    "failed_providers": results.get("failed_providers", []),
                }
                
        except Exception as e:
            logger.error(f"Failed to enable MemoryManager: {e}")
            return {"success": False, "message": str(e)}
    
    def _map_interceptors_to_providers(self, interceptors: List[str]) -> List[ProviderType]:
        """Map legacy interceptor names to provider types."""
        provider_types = []
        for interceptor in interceptors:
            if "openai" in interceptor.lower():
                provider_types.append(ProviderType.OPENAI)
            elif "anthropic" in interceptor.lower():
                provider_types.append(ProviderType.ANTHROPIC)
            elif "litellm" in interceptor.lower():
                provider_types.append(ProviderType.LITELLM)
        return list(set(provider_types))  # Remove duplicates
    
    def _get_enabled_providers(self) -> List[str]:
        """Get list of currently enabled provider names."""
        if not self.pattern_manager:
            return []
        
        status = self.pattern_manager.get_status()
        return [provider for provider in status.get("active_providers", [])]

    def disable(self) -> Dict[str, Any]:
        """
        Disable memory recording using the universal three-tier architecture.

        Returns:
            Dict containing disable results
        """
        if not self._enabled:
            return {"success": True, "message": "Already disabled"}

        if not self.pattern_manager:
            logger.error("Pattern manager not initialized")
            return {"success": False, "message": "Pattern manager not available"}

        try:
            # Disable auto-integration for all providers
            results = self.pattern_manager.disable_auto_integration()
            
            self._enabled = False

            logger.info(f"Universal MemoryManager disabled: {results['message']}")

            return {
                "success": True,
                "message": results["message"],
                "disabled_providers": results.get("disabled_providers", []),
                "disabled_interceptors": results.get("disabled_providers", []),  # For backward compatibility
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
        if not self.pattern_manager:
            return {
                "error": "Pattern manager not initialized",
                "session_id": self._session_id,
                "enabled": self._enabled,
            }
        
        # Get status from universal pattern manager
        universal_status = self.pattern_manager.get_status()
        
        # Transform for backward compatibility
        status = {}
        
        # Add session info
        universal_status["session_id"] = self._session_id
        universal_status["memory_manager_enabled"] = self._enabled
        
        # Map provider statuses to legacy format for backward compatibility
        for provider_name, patterns in universal_status.get("enabled_patterns", {}).items():
            legacy_name = f"{provider_name}_native"
            status[legacy_name] = {
                "enabled": "auto_integration" in patterns,
                "status": "active" if "auto_integration" in patterns else "available_but_not_registered",
                "method": "universal_pattern_manager",
                "session_id": self._session_id,
                "provider_type": provider_name,
                "available_patterns": patterns,
            }
        
        # Add providers that are available but not enabled
        available_providers = get_available_providers()
        for provider_type in available_providers:
            legacy_name = f"{provider_type.value}_native"
            if legacy_name not in status:
                status[legacy_name] = {
                    "enabled": False,
                    "status": "available_but_not_registered",
                    "method": "universal_pattern_manager",
                    "session_id": self._session_id,
                    "provider_type": provider_type.value,
                    "available_patterns": [],
                }
        
        # Add universal status info
        status["universal"] = universal_status
            
        return status

    def get_health(self) -> Dict[str, Any]:
        """
        Get health check of the memory management system.

        Returns:
            Dict containing health information
        """
        health = {
            "session_id": self._session_id,
            "enabled": self._enabled,
            "namespace": self.namespace,
            "user_id": self.user_id,
            "memory_filters": len(self.memory_filters),
            "conscious_ingest": self.conscious_ingest,
            "auto_ingest": self.auto_ingest,
            "database_connect": self.database_connect,
            "template": self.template,
            "pattern_manager_available": self.pattern_manager is not None,
        }
        
        # Add universal pattern manager health if available
        if self.pattern_manager:
            universal_status = self.pattern_manager.get_status()
            health.update({
                "universal_pattern_manager": {
                    "active_providers": universal_status.get("active_providers", []),
                    "enabled_patterns": universal_status.get("enabled_patterns", {}),
                    "total_patterns_tracked": universal_status.get("universal_manager", {}).get("total_patterns_tracked", 0),
                },
                "available_provider_types": [pt.value for pt in get_available_providers()],
            })
        
        return health

    # ========================
    # Universal Pattern Access Methods
    # ========================
    
    def create_wrapped_client(self, provider_type: str, **kwargs) -> Optional[Any]:
        """
        Create a wrapped client for the Wrapper Pattern (Best Practice).
        
        Args:
            provider_type: Provider type ('openai', 'anthropic', 'litellm')
            **kwargs: Provider-specific client configuration
            
        Returns:
            Wrapped client instance or None if failed
        """
        if not self.pattern_manager:
            logger.error("Pattern manager not available")
            return None
            
        try:
            # Map string to ProviderType enum
            if isinstance(provider_type, str):
                provider_enum = ProviderType(provider_type.lower())
            else:
                provider_enum = provider_type  # Already a ProviderType
            return self.pattern_manager.create_wrapped_client(provider_enum, **kwargs)
        except ValueError:
            logger.error(f"Unknown provider type: {provider_type}")
            return None
        except Exception as e:
            logger.error(f"Failed to create wrapped client: {e}")
            return None
    
    def record_manual_response(self, provider_type: str, response: Any, user_input: str = "", **kwargs) -> Optional[str]:
        """
        Record a manual response using the Manual Recording Pattern.
        
        Args:
            provider_type: Provider type ('openai', 'anthropic', 'litellm')
            response: Raw provider response
            user_input: Original user input
            **kwargs: Additional metadata
            
        Returns:
            Conversation ID or None if failed
        """
        if not self.pattern_manager:
            logger.error("Pattern manager not available")
            return None
            
        try:
            # Map string to ProviderType enum
            if isinstance(provider_type, str):
                provider_enum = ProviderType(provider_type.lower())
            else:
                provider_enum = provider_type  # Already a ProviderType
            return self.pattern_manager.record_manual_response(provider_enum, response, user_input, **kwargs)
        except ValueError:
            logger.error(f"Unknown provider type: {provider_type}")
            return None
        except Exception as e:
            logger.error(f"Failed to record manual response: {e}")
            return None

    # ========================
    # Backward Compatibility Properties
    # ========================

    @property
    def session_id(self) -> str:
        """Get session ID for backward compatibility."""
        return self._session_id

    @property
    def enabled(self) -> bool:
        """Check if enabled for backward compatibility."""
        return self._enabled

    # ========================
    # Cleanup and Context Management
    # ========================

    def cleanup(self):
        """Cleanup resources."""
        try:
            if self._enabled:
                self.disable()
            
            # Clean up universal pattern manager
            if self.pattern_manager:
                self.pattern_manager.cleanup()
                self.pattern_manager = None
                
            logger.info("UniversalMemoryManager cleanup completed")
        except Exception as e:
            logger.error(f"Error during UniversalMemoryManager cleanup: {e}")

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


# Alias for backward compatibility
MemoryManager = UniversalMemoryManager