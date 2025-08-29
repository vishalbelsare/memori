"""
Modern conversation interceptors for automatic LLM conversation recording.

This package provides a clean, modular architecture for intercepting LLM conversations
without monkey-patching. Each interceptor handles specific providers or protocols.
"""

from .base import ConversationInterceptor
from .litellm_interceptor import LiteLLMNativeInterceptor
from .openai_interceptor import OpenAIClientInterceptor
from .anthropic_interceptor import AnthropicClientInterceptor
from .http_interceptor import HTTPInterceptor
from .manager import InterceptorManager

__all__ = [
    'ConversationInterceptor',
    'LiteLLMNativeInterceptor', 
    'OpenAIClientInterceptor',
    'AnthropicClientInterceptor',
    'HTTPInterceptor',
    'InterceptorManager'
]