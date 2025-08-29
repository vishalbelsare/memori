"""
Base conversation interceptor class for all interceptor implementations.
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from ..core.memory import Memori


class ConversationInterceptor(ABC):
    """Base class for conversation interceptors"""

    def __init__(self, memori_instance: "Memori"):
        self.memori = memori_instance
        self._enabled = False
        self._lock = threading.RLock()
        # Circuit breaker pattern for error handling
        self._failure_count = 0
        self._last_failure_time = 0
        self._max_failures = 5
        self._failure_reset_timeout = 300  # 5 minutes

    @abstractmethod
    def enable(self) -> bool:
        """Enable interception. Returns True if successful."""
        pass

    @abstractmethod
    def disable(self) -> bool:
        """Disable interception. Returns True if successful."""
        pass

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def _record_failure(self):
        """Record a failure for circuit breaker logic"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._max_failures:
            logger.warning(
                f"{self.name}: Too many failures ({self._failure_count}), temporarily disabling"
            )

    def _record_success(self):
        """Record a successful operation"""
        if self._failure_count > 0:
            logger.info(f"{self.name}: Operation successful, resetting failure count")
            self._failure_count = 0  # Reset on success

    def _should_allow_operation(self) -> bool:
        """Check if operations should be allowed based on failure history"""
        if self._failure_count < self._max_failures:
            return True

        # Check if enough time has passed to reset
        if time.time() - self._last_failure_time > self._failure_reset_timeout:
            self._failure_count = 0
            return True

        return False

    def health_check(self) -> dict:
        """Return health status of the interceptor"""
        return {
            "name": self.name,
            "enabled": self._enabled,
            "failure_count": self._failure_count,
            "operational": self._should_allow_operation(),
        }
