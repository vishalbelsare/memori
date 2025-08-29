"""
Anthropic client interceptor using clean subclassing instead of monkey-patching.
"""

import weakref
from typing import TYPE_CHECKING

from loguru import logger

from .base import ConversationInterceptor

if TYPE_CHECKING:
    from ..core.memory import Memori


class AnthropicClientInterceptor(ConversationInterceptor):
    """Clean Anthropic client interception using subclassing"""

    def __init__(self, memori_instance: "Memori"):
        super().__init__(memori_instance)

    def enable(self) -> bool:
        """Enable Anthropic client interception"""
        with self._lock:
            if self._enabled:
                return True

            try:
                import anthropic

                # Store original classes
                if not hasattr(anthropic, "_memori_original_Anthropic"):
                    anthropic._memori_original_Anthropic = anthropic.Anthropic
                    anthropic._memori_original_AsyncAnthropic = anthropic.AsyncAnthropic

                # Replace with wrapped versions
                anthropic.Anthropic = self._create_wrapped_anthropic_client(
                    anthropic._memori_original_Anthropic
                )
                anthropic.AsyncAnthropic = self._create_wrapped_async_anthropic_client(
                    anthropic._memori_original_AsyncAnthropic
                )

                self._enabled = True
                logger.debug("Anthropic client interceptor enabled")
                return True

            except ImportError:
                logger.debug("Anthropic not available")
                return False
            except Exception as e:
                logger.error(f"Failed to enable Anthropic interceptor: {e}")
                return False

    def disable(self) -> bool:
        """Disable Anthropic client interception"""
        with self._lock:
            if not self._enabled:
                return True

            try:
                import anthropic

                # Restore original classes
                if hasattr(anthropic, "_memori_original_Anthropic"):
                    anthropic.Anthropic = anthropic._memori_original_Anthropic
                    anthropic.AsyncAnthropic = anthropic._memori_original_AsyncAnthropic
                    delattr(anthropic, "_memori_original_Anthropic")
                    delattr(anthropic, "_memori_original_AsyncAnthropic")

                self._enabled = False
                logger.debug("Anthropic client interceptor disabled")
                return True

            except Exception as e:
                logger.error(f"Failed to disable Anthropic interceptor: {e}")
                return False

    def _create_wrapped_anthropic_client(self, original_class):
        """Create wrapped Anthropic client class"""
        memori = self.memori

        class MemoriAnthropicClient(original_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Use weak reference to avoid circular references
                self._memori_ref = weakref.ref(memori)

            @property
            def _memori(self):
                """Get memori instance from weak reference with graceful degradation"""
                memori_instance = self._memori_ref()
                if memori_instance is None:
                    logger.warning(
                        f"{self.__class__.__name__}: Memori instance garbage collected, disabling interception"
                    )
                    return None
                return memori_instance

            @property
            def messages(self):
                if not hasattr(self, "_memori_messages"):
                    original_messages = super().messages
                    self._memori_messages = self._wrap_messages(original_messages)
                return self._memori_messages

            def _wrap_messages(self, original_messages):
                """Wrap messages methods"""

                class WrappedMessages:
                    def __init__(self, original):
                        self._original = original

                    def create(self, **kwargs):
                        # Inject context if enabled (auto_ingest OR conscious_ingest)
                        if memori.is_enabled and (
                            memori.auto_ingest or memori.conscious_ingest
                        ):
                            kwargs = memori._inject_anthropic_context(kwargs)

                        # Make the call
                        response = self._original.create(**kwargs)

                        # Always record if enabled (regardless of ingest mode)
                        if memori.is_enabled:
                            memori._record_anthropic_conversation(kwargs, response)

                        return response

                    def __getattr__(self, name):
                        return getattr(self._original, name)

                return WrappedMessages(original_messages)

            def __getattr__(self, name):
                return getattr(super(), name)

        return MemoriAnthropicClient

    def _create_wrapped_async_anthropic_client(self, original_class):
        """Create wrapped async Anthropic client"""
        memori = self.memori

        class MemoriAsyncAnthropicClient(original_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Use weak reference to avoid circular references
                self._memori_ref = weakref.ref(memori)

            @property
            def _memori(self):
                """Get memori instance from weak reference with graceful degradation"""
                memori_instance = self._memori_ref()
                if memori_instance is None:
                    logger.warning(
                        f"{self.__class__.__name__}: Memori instance garbage collected, disabling interception"
                    )
                    return None
                return memori_instance

            @property
            def messages(self):
                if not hasattr(self, "_memori_messages"):
                    original_messages = super().messages
                    self._memori_messages = self._wrap_async_messages(original_messages)
                return self._memori_messages

            def _wrap_async_messages(self, original_messages):
                """Wrap async messages methods"""

                class WrappedAsyncMessages:
                    def __init__(self, original):
                        self._original = original

                    async def create(self, **kwargs):
                        # Inject context if enabled (auto_ingest OR conscious_ingest)
                        if memori.is_enabled and (
                            memori.auto_ingest or memori.conscious_ingest
                        ):
                            kwargs = memori._inject_anthropic_context(kwargs)

                        # Make the async call
                        response = await self._original.create(**kwargs)

                        # Always record if enabled (regardless of ingest mode)
                        if memori.is_enabled:
                            memori._record_anthropic_conversation(kwargs, response)

                        return response

                    def __getattr__(self, name):
                        return getattr(self._original, name)

                return WrappedAsyncMessages(original_messages)

            def __getattr__(self, name):
                return getattr(super(), name)

        return MemoriAsyncAnthropicClient
