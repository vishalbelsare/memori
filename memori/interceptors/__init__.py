"""
Modern conversation interceptors for automatic LLM conversation recording.

This package provides a clean, modular architecture for intercepting LLM conversations
without monkey-patching. Each interceptor handles specific providers or protocols.
"""

from .anthropic_interceptor import AnthropicClientInterceptor
from .base import ConversationInterceptor
from .http_interceptor import HTTPInterceptor
from .litellm_interceptor import LiteLLMNativeInterceptor
from .manager import InterceptorManager
from .openai_interceptor import OpenAIClientInterceptor

__all__ = [
    "ConversationInterceptor",
    "LiteLLMNativeInterceptor",
    "OpenAIClientInterceptor",
    "AnthropicClientInterceptor",
    "HTTPInterceptor",
    "InterceptorManager",
]
