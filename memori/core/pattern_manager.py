"""
Universal Pattern Manager for Three-Tier Architecture

This module manages the three patterns (Auto-Integration, Wrapper, Manual Recording)
across all LLM providers in a unified way.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import time

from loguru import logger

from .providers_base import (
    BaseProvider, ProviderType, PatternType, 
    ProviderRequest, ProviderResponse,
    UniversalContextInjector, UniversalResponseParser,
    provider_registry
)


@dataclass
class PatternStatus:
    """Status information for a pattern."""
    enabled: bool
    provider_type: ProviderType
    pattern_type: PatternType
    last_used: Optional[float] = None
    call_count: int = 0
    error_count: int = 0


class UniversalPatternManager:
    """
    Universal manager for all three-tier architecture patterns across all providers.
    
    This class provides a unified interface for:
    1. Auto-Integration Pattern (Magic): Automatic interception
    2. Wrapper Pattern (Best Practice): Wrapped clients  
    3. Manual Recording Pattern (Manual Utility): Manual recording
    
    It works consistently across OpenAI, Anthropic, LiteLLM, and any future providers.
    """
    
    def __init__(self, memori_instance):
        """
        Initialize the universal pattern manager.
        
        Args:
            memori_instance: The parent Memori instance
        """
        self.memori_instance = memori_instance
        self.context_injector = UniversalContextInjector(memori_instance)
        self.response_parser = UniversalResponseParser(memori_instance)
        
        # Track pattern statuses
        self._pattern_statuses: Dict[str, PatternStatus] = {}
        
        # Track active providers
        self._active_providers: Dict[ProviderType, BaseProvider] = {}
        
        # Track enabled patterns per provider
        self._enabled_patterns: Dict[ProviderType, Set[PatternType]] = {}
    
    # ========================
    # Pattern Management
    # ========================
    
    def enable_auto_integration(self, provider_types: Optional[List[ProviderType]] = None) -> Dict[str, Any]:
        """
        Enable Auto-Integration Pattern (Magic) for specified providers.
        
        Args:
            provider_types: List of provider types to enable. If None, enables for all available providers.
            
        Returns:
            Dict with enablement results
        """
        if provider_types is None:
            provider_types = [ProviderType.OPENAI, ProviderType.ANTHROPIC, ProviderType.LITELLM]
        
        results = {
            "success": True,
            "enabled_providers": [],
            "failed_providers": [],
            "message": ""
        }
        
        for provider_type in provider_types:
            try:
                provider = self._get_or_create_provider(provider_type)
                if provider is None:
                    results["failed_providers"].append(f"{provider_type.value} (not available)")
                    continue
                
                # Enable auto-integration for this provider
                if provider.setup_auto_integration():
                    self._add_enabled_pattern(provider_type, PatternType.AUTO_INTEGRATION)
                    results["enabled_providers"].append(provider_type.value)
                    
                    # Update status
                    self._update_pattern_status(provider_type, PatternType.AUTO_INTEGRATION, enabled=True)
                    
                    logger.info(f"Auto-integration enabled for {provider_type.value}")
                else:
                    results["failed_providers"].append(f"{provider_type.value} (setup failed)")
                    
            except Exception as e:
                results["failed_providers"].append(f"{provider_type.value} (error: {e})")
                logger.error(f"Failed to enable auto-integration for {provider_type.value}: {e}")
        
        if not results["enabled_providers"]:
            results["success"] = False
            results["message"] = "No providers were successfully enabled"
        else:
            results["message"] = f"Auto-integration enabled for: {', '.join(results['enabled_providers'])}"
        
        return results
    
    def disable_auto_integration(self, provider_types: Optional[List[ProviderType]] = None) -> Dict[str, Any]:
        """
        Disable Auto-Integration Pattern for specified providers.
        
        Args:
            provider_types: List of provider types to disable. If None, disables for all.
            
        Returns:
            Dict with disable results
        """
        if provider_types is None:
            provider_types = list(self._active_providers.keys())
        
        results = {
            "success": True,
            "disabled_providers": [],
            "failed_providers": [],
            "message": ""
        }
        
        for provider_type in provider_types:
            try:
                provider = self._active_providers.get(provider_type)
                if provider is None:
                    continue  # Not active, nothing to disable
                
                # Disable auto-integration for this provider
                if provider.teardown_auto_integration():
                    self._remove_enabled_pattern(provider_type, PatternType.AUTO_INTEGRATION)
                    results["disabled_providers"].append(provider_type.value)
                    
                    # Update status
                    self._update_pattern_status(provider_type, PatternType.AUTO_INTEGRATION, enabled=False)
                    
                    logger.info(f"Auto-integration disabled for {provider_type.value}")
                else:
                    results["failed_providers"].append(f"{provider_type.value} (teardown failed)")
                    
            except Exception as e:
                results["failed_providers"].append(f"{provider_type.value} (error: {e})")
                logger.error(f"Failed to disable auto-integration for {provider_type.value}: {e}")
        
        if results["disabled_providers"]:
            results["message"] = f"Auto-integration disabled for: {', '.join(results['disabled_providers'])}"
        else:
            results["message"] = "No providers were disabled"
        
        return results
    
    def create_wrapped_client(self, provider_type: ProviderType, **kwargs) -> Optional[Any]:
        """
        Create a wrapped client for the Wrapper Pattern (Best Practice).
        
        Args:
            provider_type: Type of provider to create wrapped client for
            **kwargs: Provider-specific client configuration
            
        Returns:
            Wrapped client instance or None if failed
        """
        try:
            provider = self._get_or_create_provider(provider_type)
            if provider is None:
                logger.error(f"Provider {provider_type.value} not available for wrapped client")
                return None
            
            # Create wrapped client
            wrapped_client = provider.create_wrapped_client(**kwargs)
            if wrapped_client is not None:
                self._add_enabled_pattern(provider_type, PatternType.WRAPPER)
                self._update_pattern_status(provider_type, PatternType.WRAPPER, enabled=True)
                logger.info(f"Created wrapped client for {provider_type.value}")
            
            return wrapped_client
            
        except Exception as e:
            logger.error(f"Failed to create wrapped client for {provider_type.value}: {e}")
            return None
    
    def record_manual_response(self, provider_type: ProviderType, response: Any, user_input: str = "", **kwargs) -> Optional[str]:
        """
        Record a manual response using the Manual Recording Pattern.
        
        Args:
            provider_type: Type of provider that generated the response
            response: Raw provider response
            user_input: Original user input
            **kwargs: Additional metadata
            
        Returns:
            Conversation ID or None if failed
        """
        try:
            provider = self._get_or_create_provider(provider_type)
            if provider is None:
                logger.error(f"Provider {provider_type.value} not available for manual recording")
                return None
            
            # Parse the response
            provider_response = provider.parse_manual_response(response, user_input, **kwargs)
            
            # Record the conversation
            conversation_id = self.response_parser.record_conversation(provider_response)
            
            # Update pattern usage
            self._add_enabled_pattern(provider_type, PatternType.MANUAL_RECORDING)
            self._update_pattern_status(provider_type, PatternType.MANUAL_RECORDING, enabled=True)
            self._increment_pattern_usage(provider_type, PatternType.MANUAL_RECORDING)
            
            logger.debug(f"Manually recorded conversation {conversation_id} for {provider_type.value}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to manually record for {provider_type.value}: {e}")
            self._increment_pattern_error(provider_type, PatternType.MANUAL_RECORDING)
            return None
    
    # ========================
    # Universal Request/Response Handling
    # ========================
    
    def handle_request(self, provider_type: ProviderType, pattern_type: PatternType, 
                      request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a universal request for any provider and pattern.
        
        This method is called by provider-specific interceptors and wrappers
        to ensure consistent behavior across all patterns.
        
        Args:
            provider_type: Type of provider making the request
            pattern_type: Pattern being used
            request_data: Raw request data
            
        Returns:
            Modified request data with context injected
        """
        try:
            provider = self._active_providers.get(provider_type)
            if provider is None:
                logger.warning(f"Provider {provider_type.value} not active, skipping request handling")
                return request_data
            
            # Create standardized request
            provider_request = provider.create_provider_request(request_data, pattern_type)
            
            # Inject context if enabled
            if self.memori_instance.is_enabled and (self.memori_instance.conscious_ingest or self.memori_instance.auto_ingest):
                provider_request = self.context_injector.inject_context(provider_request)
            
            # Let provider customize the request
            provider_request = provider.inject_context(provider_request)
            
            # Update usage tracking
            self._increment_pattern_usage(provider_type, pattern_type)
            
            return provider_request.original_kwargs
            
        except Exception as e:
            logger.error(f"Request handling failed for {provider_type.value} {pattern_type.value}: {e}")
            self._increment_pattern_error(provider_type, pattern_type)
            return request_data
    
    def handle_response(self, provider_type: ProviderType, pattern_type: PatternType,
                       response: Any, request_data: Dict[str, Any]) -> Optional[str]:
        """
        Handle a universal response for any provider and pattern.
        
        This method is called by provider-specific interceptors and wrappers
        to ensure consistent recording across all patterns.
        
        Args:
            provider_type: Type of provider that generated the response
            pattern_type: Pattern being used
            response: Raw provider response
            request_data: Original request data
            
        Returns:
            Conversation ID or None if failed
        """
        try:
            provider = self._active_providers.get(provider_type)
            if provider is None:
                logger.warning(f"Provider {provider_type.value} not active, skipping response handling")
                return None
            
            # Parse the response
            provider_response = provider.parse_response(response, request_data)
            provider_response.pattern_type = pattern_type
            
            # Record the conversation
            conversation_id = self.response_parser.record_conversation(provider_response)
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Response handling failed for {provider_type.value} {pattern_type.value}: {e}")
            self._increment_pattern_error(provider_type, pattern_type)
            return None
    
    # ========================
    # Status and Management
    # ========================
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all patterns and providers."""
        status = {
            "active_providers": list(self._active_providers.keys()),
            "enabled_patterns": {},
            "pattern_stats": {},
            "universal_manager": {
                "context_injector_available": self.context_injector is not None,
                "response_parser_available": self.response_parser is not None,
                "total_patterns_tracked": len(self._pattern_statuses),
            }
        }
        
        # Add provider-specific pattern status
        for provider_type, patterns in self._enabled_patterns.items():
            status["enabled_patterns"][provider_type.value] = [p.value for p in patterns]
        
        # Add detailed pattern statistics
        for key, pattern_status in self._pattern_statuses.items():
            status["pattern_stats"][key] = {
                "enabled": pattern_status.enabled,
                "provider": pattern_status.provider_type.value,
                "pattern": pattern_status.pattern_type.value,
                "call_count": pattern_status.call_count,
                "error_count": pattern_status.error_count,
                "last_used": pattern_status.last_used,
            }
        
        return status
    
    def cleanup(self):
        """Clean up all patterns and providers."""
        try:
            # Disable all auto-integration patterns
            self.disable_auto_integration()
            
            # Clear all tracking
            self._pattern_statuses.clear()
            self._enabled_patterns.clear()
            self._active_providers.clear()
            
            logger.info("Universal pattern manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error during pattern manager cleanup: {e}")
    
    # ========================
    # Internal Helper Methods
    # ========================
    
    def _get_or_create_provider(self, provider_type: ProviderType) -> Optional[BaseProvider]:
        """Get existing provider or create new one."""
        if provider_type in self._active_providers:
            return self._active_providers[provider_type]
        
        # Create new provider instance
        provider = provider_registry.get_provider(provider_type, self.memori_instance)
        if provider is not None:
            self._active_providers[provider_type] = provider
        
        return provider
    
    def _add_enabled_pattern(self, provider_type: ProviderType, pattern_type: PatternType):
        """Add a pattern to the enabled patterns set."""
        if provider_type not in self._enabled_patterns:
            self._enabled_patterns[provider_type] = set()
        self._enabled_patterns[provider_type].add(pattern_type)
    
    def _remove_enabled_pattern(self, provider_type: ProviderType, pattern_type: PatternType):
        """Remove a pattern from the enabled patterns set."""
        if provider_type in self._enabled_patterns:
            self._enabled_patterns[provider_type].discard(pattern_type)
            if not self._enabled_patterns[provider_type]:
                del self._enabled_patterns[provider_type]
    
    def _update_pattern_status(self, provider_type: ProviderType, pattern_type: PatternType, enabled: bool):
        """Update pattern status tracking."""
        key = f"{provider_type.value}_{pattern_type.value}"
        
        if key not in self._pattern_statuses:
            self._pattern_statuses[key] = PatternStatus(
                enabled=enabled,
                provider_type=provider_type,
                pattern_type=pattern_type,
                call_count=0,
                error_count=0,
            )
        else:
            self._pattern_statuses[key].enabled = enabled
    
    def _increment_pattern_usage(self, provider_type: ProviderType, pattern_type: PatternType):
        """Increment usage count for a pattern."""
        key = f"{provider_type.value}_{pattern_type.value}"
        if key in self._pattern_statuses:
            self._pattern_statuses[key].call_count += 1
            self._pattern_statuses[key].last_used = time.time()
    
    def _increment_pattern_error(self, provider_type: ProviderType, pattern_type: PatternType):
        """Increment error count for a pattern."""
        key = f"{provider_type.value}_{pattern_type.value}"
        if key in self._pattern_statuses:
            self._pattern_statuses[key].error_count += 1