"""
Manager class for coordinating multiple conversation interceptors.
"""

import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, List

from loguru import logger

from .anthropic_interceptor import AnthropicClientInterceptor
from .base import ConversationInterceptor
from .http_interceptor import HTTPInterceptor
from .litellm_interceptor import LiteLLMNativeInterceptor
from .openai_interceptor import OpenAIClientInterceptor

if TYPE_CHECKING:
    from ..core.memory import Memori


class InterceptorManager:
    """Manages multiple conversation interceptors with fallback strategy"""

    def __init__(self, memori_instance: "Memori"):
        self.memori = memori_instance
        self.interceptors: List[ConversationInterceptor] = [
            LiteLLMNativeInterceptor(memori_instance),
            OpenAIClientInterceptor(memori_instance),
            AnthropicClientInterceptor(memori_instance),
            HTTPInterceptor(memori_instance),
        ]
        self._enabled_interceptors: List[ConversationInterceptor] = []
        self._lock = threading.RLock()

    def enable(self, methods: List[str] = None) -> Dict[str, bool]:
        """
        Enable conversation interception with fallback strategy

        Args:
            methods: List of methods to try ['native', 'openai', 'anthropic', 'http', 'all']
                    None defaults to ['native', 'openai', 'anthropic', 'http']

        Returns:
            Dict mapping interceptor names to success status
        """
        with self._lock:
            if methods is None:
                methods = ["native", "openai", "anthropic", "http"]

            results = {}

            # Map method names to interceptor types
            method_mapping = {
                "native": [LiteLLMNativeInterceptor],
                "litellm": [LiteLLMNativeInterceptor],
                "openai": [OpenAIClientInterceptor],
                "anthropic": [AnthropicClientInterceptor],
                "http": [HTTPInterceptor],
                "all": [
                    LiteLLMNativeInterceptor,
                    OpenAIClientInterceptor,
                    AnthropicClientInterceptor,
                    HTTPInterceptor,
                ],
            }

            # Collect interceptors to enable
            interceptors_to_enable = []
            for method in methods:
                if method in method_mapping:
                    interceptors_to_enable.extend(method_mapping[method])

            # Enable selected interceptors
            for interceptor in self.interceptors:
                if type(interceptor) in interceptors_to_enable:
                    success = interceptor.enable()
                    results[interceptor.name] = success
                    if success:
                        self._enabled_interceptors.append(interceptor)
                        logger.debug(f"Enabled {interceptor.name}")
                    else:
                        logger.debug(f"Failed to enable {interceptor.name}")

            return results

    def disable(self) -> Dict[str, bool]:
        """Disable all enabled interceptors"""
        with self._lock:
            results = {}

            for interceptor in self._enabled_interceptors[
                :
            ]:  # Copy list to avoid modification during iteration
                success = interceptor.disable()
                results[interceptor.name] = success
                if success:
                    self._enabled_interceptors.remove(interceptor)
                    logger.debug(f"Disabled {interceptor.name}")
                else:
                    logger.warning(f"Failed to disable {interceptor.name}")

            return results

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive status of all interceptors"""
        status = {}
        for interceptor in self.interceptors:
            interceptor_status = {
                "enabled": interceptor.is_enabled,
                "available": self._check_interceptor_availability(interceptor),
                "type": type(interceptor).__name__,
                "health": interceptor.health_check(),
            }
            status[interceptor.name] = interceptor_status
        return status

    def get_interceptor_status(self) -> Dict[str, Any]:
        """Get summary status of interceptor system"""
        enabled_names = [i.name for i in self._enabled_interceptors]
        available_names = [
            i.name for i in self.interceptors if self._check_interceptor_availability(i)
        ]

        return {
            "enabled": enabled_names,
            "available": available_names,
            "total": len(self.interceptors),
            "enabled_count": len(self._enabled_interceptors),
        }

    def _check_interceptor_availability(
        self, interceptor: ConversationInterceptor
    ) -> bool:
        """Check if interceptor's dependencies are available"""
        try:
            if isinstance(interceptor, LiteLLMNativeInterceptor):
                import litellm

                return True
            elif isinstance(interceptor, OpenAIClientInterceptor):
                import openai

                return True
            elif isinstance(interceptor, AnthropicClientInterceptor):
                import anthropic

                return True
            elif isinstance(interceptor, HTTPInterceptor):
                # Check if either httpx or requests is available
                try:
                    import httpx

                    return True
                except ImportError:
                    try:
                        import requests

                        return True
                    except ImportError:
                        return False
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of interceptor system"""
        health = {
            "overall_status": "healthy",
            "enabled_count": len(self._enabled_interceptors),
            "total_count": len(self.interceptors),
            "issues": [],
            "recommendations": [],
        }

        # Check each interceptor
        for interceptor in self.interceptors:
            if interceptor.is_enabled:
                # Check if interceptor is working properly
                if not self._check_interceptor_availability(interceptor):
                    health["issues"].append(
                        f"{interceptor.name} is enabled but dependencies are not available"
                    )
                    health["overall_status"] = "degraded"

        # Check if any interceptors are enabled
        if len(self._enabled_interceptors) == 0:
            health["issues"].append("No interceptors are currently enabled")
            health["recommendations"].append(
                "Enable interceptors using enable() method"
            )
            health["overall_status"] = "unhealthy"

        # Check for optimal configuration
        litellm_enabled = any(
            isinstance(i, LiteLLMNativeInterceptor) and i.is_enabled
            for i in self.interceptors
        )
        if not litellm_enabled:
            health["recommendations"].append(
                "Consider enabling LiteLLM interceptor for best performance"
            )

        return health

    @contextmanager
    def temporary_enable(self, methods: List[str] = None):
        """Context manager for temporary interception"""
        with self._lock:
            original_enabled = self._enabled_interceptors[:]

            try:
                self.enable(methods)
                yield self
            finally:
                # Restore original state
                self.disable()
                for interceptor in original_enabled:
                    interceptor.enable()
                    self._enabled_interceptors.append(interceptor)

    def get_enabled_interceptors(self) -> List[ConversationInterceptor]:
        """Get list of currently enabled interceptors"""
        return self._enabled_interceptors[:]

    def is_any_enabled(self) -> bool:
        """Check if any interceptors are enabled"""
        return len(self._enabled_interceptors) > 0
