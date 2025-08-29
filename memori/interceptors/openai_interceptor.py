"""
OpenAI client interceptor using clean subclassing instead of monkey-patching.
"""

import weakref
from typing import TYPE_CHECKING

from loguru import logger

from .base import ConversationInterceptor

if TYPE_CHECKING:
    from ..core.memory import Memori


class OpenAIClientInterceptor(ConversationInterceptor):
    """Clean OpenAI client interception using subclassing instead of monkey-patching"""

    def __init__(self, memori_instance: "Memori"):
        super().__init__(memori_instance)
        self._wrapped_clients = []

    def enable(self) -> bool:
        """Enable OpenAI client interception"""
        with self._lock:
            if self._enabled:
                return True

            try:
                import openai

                # Store original classes for restoration
                if not hasattr(openai, "_memori_original_OpenAI"):
                    openai._memori_original_OpenAI = openai.OpenAI
                    openai._memori_original_AsyncOpenAI = openai.AsyncOpenAI

                # Replace with wrapped versions
                openai.OpenAI = self._create_wrapped_openai_client(
                    openai._memori_original_OpenAI
                )
                openai.AsyncOpenAI = self._create_wrapped_async_openai_client(
                    openai._memori_original_AsyncOpenAI
                )

                # Also handle Azure if available
                try:
                    from openai import AsyncAzureOpenAI, AzureOpenAI

                    if not hasattr(openai, "_memori_original_AzureOpenAI"):
                        openai._memori_original_AzureOpenAI = AzureOpenAI
                        openai._memori_original_AsyncAzureOpenAI = AsyncAzureOpenAI

                    openai.AzureOpenAI = self._create_wrapped_azure_client(
                        openai._memori_original_AzureOpenAI
                    )
                    openai.AsyncAzureOpenAI = self._create_wrapped_async_azure_client(
                        openai._memori_original_AsyncAzureOpenAI
                    )
                except ImportError:
                    pass  # Azure not available

                self._enabled = True
                logger.debug("OpenAI client interceptor enabled")
                return True

            except ImportError:
                logger.debug("OpenAI not available")
                return False
            except Exception as e:
                logger.error(f"Failed to enable OpenAI interceptor: {e}")
                return False

    def disable(self) -> bool:
        """Disable OpenAI client interception"""
        with self._lock:
            if not self._enabled:
                return True

            try:
                import openai

                # Restore original classes
                if hasattr(openai, "_memori_original_OpenAI"):
                    openai.OpenAI = openai._memori_original_OpenAI
                    openai.AsyncOpenAI = openai._memori_original_AsyncOpenAI
                    delattr(openai, "_memori_original_OpenAI")
                    delattr(openai, "_memori_original_AsyncOpenAI")

                # Restore Azure if available
                if hasattr(openai, "_memori_original_AzureOpenAI"):
                    openai.AzureOpenAI = openai._memori_original_AzureOpenAI
                    openai.AsyncAzureOpenAI = openai._memori_original_AsyncAzureOpenAI
                    delattr(openai, "_memori_original_AzureOpenAI")
                    delattr(openai, "_memori_original_AsyncAzureOpenAI")

                self._enabled = False
                logger.debug("OpenAI client interceptor disabled")
                return True

            except Exception as e:
                logger.error(f"Failed to disable OpenAI interceptor: {e}")
                return False

    def _create_wrapped_openai_client(self, original_class):
        """Create wrapped OpenAI client class"""
        memori = self.memori

        class MemoriOpenAIClient(original_class):
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
            def chat(self):
                if not hasattr(self, "_memori_chat"):
                    original_chat = super().chat
                    self._memori_chat = self._wrap_chat_completions(original_chat)
                return self._memori_chat

            def _wrap_chat_completions(self, original_chat):
                """Wrap chat completions methods"""

                class WrappedChatCompletions:
                    def __init__(self, original):
                        self._original = original

                    @property
                    def completions(self):
                        if not hasattr(self, "_memori_completions"):
                            self._memori_completions = self._wrap_completions_create(
                                self._original.completions
                            )
                        return self._memori_completions

                    def _wrap_completions_create(self, original_completions):
                        """Wrap the create method"""

                        class WrappedCompletions:
                            def __init__(self, original, parent_client):
                                self._original = original
                                self._parent_client = parent_client

                            def create(self, **kwargs):
                                # Get memori instance safely from parent
                                try:
                                    memori_instance = self._parent_client._memori
                                    if not memori_instance:
                                        return self._original.create(
                                            **kwargs
                                        )  # Gracefully fallback

                                    # Inject context if enabled (auto_ingest OR conscious_ingest)
                                    if memori_instance.is_enabled and (
                                        memori_instance.auto_ingest
                                        or memori_instance.conscious_ingest
                                    ):
                                        kwargs = memori_instance._inject_openai_context(
                                            kwargs
                                        )

                                    # Make the call
                                    response = self._original.create(**kwargs)

                                    # Always record if enabled (regardless of ingest mode)
                                    if memori_instance.is_enabled:
                                        memori_instance._record_openai_conversation(
                                            kwargs, response
                                        )

                                    return response
                                except Exception:
                                    # If anything fails, fallback to original behavior
                                    return self._original.create(**kwargs)

                            def __getattr__(self, name):
                                return getattr(self._original, name)

                        return WrappedCompletions(original_completions, self)

                    def __getattr__(self, name):
                        return getattr(self._original, name)

                return WrappedChatCompletions(original_chat)

            def __getattr__(self, name):
                return getattr(super(), name)

        return MemoriOpenAIClient

    def _create_wrapped_async_openai_client(self, original_class):
        """Create wrapped async OpenAI client class"""
        memori = self.memori

        class MemoriAsyncOpenAIClient(original_class):
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
            def chat(self):
                if not hasattr(self, "_memori_chat"):
                    original_chat = super().chat
                    self._memori_chat = self._wrap_async_chat_completions(original_chat)
                return self._memori_chat

            def _wrap_async_chat_completions(self, original_chat):
                """Wrap async chat completions methods"""

                class WrappedAsyncChatCompletions:
                    def __init__(self, original):
                        self._original = original

                    @property
                    def completions(self):
                        if not hasattr(self, "_memori_completions"):
                            self._memori_completions = (
                                self._wrap_async_completions_create(
                                    self._original.completions
                                )
                            )
                        return self._memori_completions

                    def _wrap_async_completions_create(self, original_completions):
                        """Wrap the async create method"""

                        class WrappedAsyncCompletions:
                            def __init__(self, original):
                                self._original = original

                            async def create(self, **kwargs):
                                # Inject context if enabled (auto_ingest OR conscious_ingest)
                                if memori.is_enabled and (
                                    memori.auto_ingest or memori.conscious_ingest
                                ):
                                    kwargs = memori._inject_openai_context(kwargs)

                                # Make the async call
                                response = await self._original.create(**kwargs)

                                # Always record if enabled (regardless of ingest mode)
                                if memori.is_enabled:
                                    memori._record_openai_conversation(kwargs, response)

                                return response

                            def __getattr__(self, name):
                                return getattr(self._original, name)

                        return WrappedAsyncCompletions(original_completions)

                    def __getattr__(self, name):
                        return getattr(self._original, name)

                return WrappedAsyncChatCompletions(original_chat)

            def __getattr__(self, name):
                return getattr(super(), name)

        return MemoriAsyncOpenAIClient

    def _create_wrapped_azure_client(self, original_class):
        """Create wrapped Azure OpenAI client"""
        return self._create_wrapped_openai_client(original_class)

    def _create_wrapped_async_azure_client(self, original_class):
        """Create wrapped async Azure OpenAI client"""
        return self._create_wrapped_async_openai_client(original_class)
