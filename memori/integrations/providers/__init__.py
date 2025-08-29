"""
Provider Registration and Initialization

This module registers all available providers with the global provider registry
and provides convenience functions for initializing the unified three-tier architecture.
"""

from loguru import logger

from ...core.providers_base import ProviderType, provider_registry

# Import all provider implementations
try:
    from .openai_provider import OpenAIProvider
    OPENAI_PROVIDER_AVAILABLE = True
except ImportError as e:
    OPENAI_PROVIDER_AVAILABLE = False
    logger.debug(f"OpenAI provider not available: {e}")

try:
    from .anthropic_provider import AnthropicProvider
    ANTHROPIC_PROVIDER_AVAILABLE = True
except ImportError as e:
    ANTHROPIC_PROVIDER_AVAILABLE = False
    logger.debug(f"Anthropic provider not available: {e}")

try:
    from .litellm_provider import LiteLLMProvider
    LITELLM_PROVIDER_AVAILABLE = True
except ImportError as e:
    LITELLM_PROVIDER_AVAILABLE = False
    logger.debug(f"LiteLLM provider not available: {e}")


def register_all_providers():
    """Register all available providers with the global registry."""
    providers_registered = []
    
    # Register OpenAI provider
    if OPENAI_PROVIDER_AVAILABLE:
        try:
            provider_registry.register_provider(ProviderType.OPENAI, OpenAIProvider)
            providers_registered.append("OpenAI")
        except Exception as e:
            logger.warning(f"Failed to register OpenAI provider: {e}")
    
    # Register Anthropic provider
    if ANTHROPIC_PROVIDER_AVAILABLE:
        try:
            provider_registry.register_provider(ProviderType.ANTHROPIC, AnthropicProvider)
            providers_registered.append("Anthropic")
        except Exception as e:
            logger.warning(f"Failed to register Anthropic provider: {e}")
    
    # Register LiteLLM provider
    if LITELLM_PROVIDER_AVAILABLE:
        try:
            provider_registry.register_provider(ProviderType.LITELLM, LiteLLMProvider)
            providers_registered.append("LiteLLM")
        except Exception as e:
            logger.warning(f"Failed to register LiteLLM provider: {e}")
    
    if providers_registered:
        logger.info(f"Registered providers: {', '.join(providers_registered)}")
    else:
        logger.warning("No providers were registered")
    
    return providers_registered


def get_available_providers():
    """Get list of available provider types."""
    available = []
    
    if OPENAI_PROVIDER_AVAILABLE:
        available.append(ProviderType.OPENAI)
    if ANTHROPIC_PROVIDER_AVAILABLE:
        available.append(ProviderType.ANTHROPIC)
    if LITELLM_PROVIDER_AVAILABLE:
        available.append(ProviderType.LITELLM)
    
    return available


# Auto-register providers when module is imported
_providers_registered = register_all_providers()

# Export provider classes for direct use if needed
__all__ = [
    'provider_registry',
    'register_all_providers',
    'get_available_providers',
    'OPENAI_PROVIDER_AVAILABLE',
    'ANTHROPIC_PROVIDER_AVAILABLE', 
    'LITELLM_PROVIDER_AVAILABLE',
]

# Conditionally export provider classes
if OPENAI_PROVIDER_AVAILABLE:
    __all__.append('OpenAIProvider')
if ANTHROPIC_PROVIDER_AVAILABLE:
    __all__.append('AnthropicProvider')
if LITELLM_PROVIDER_AVAILABLE:
    __all__.append('LiteLLMProvider')