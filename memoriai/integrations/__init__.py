"""
Integration modules for auto-recording LLM conversations
"""

from typing import Dict, Any, List

# Import all integrations
from . import openai_integration
from . import litellm_integration
from . import anthropic_integration

# Available integrations
AVAILABLE_INTEGRATIONS = {
    'openai': openai_integration,
    'litellm': litellm_integration, 
    'anthropic': anthropic_integration
}


def install_all_hooks():
    """Install hooks for all available integrations"""
    for name, integration in AVAILABLE_INTEGRATIONS.items():
        try:
            hook_func = getattr(integration, f'install_{name}_hooks')
            hook_func()
        except Exception as e:
            print(f"Failed to install {name} hooks: {e}")


def uninstall_all_hooks():
    """Uninstall hooks for all integrations"""
    for name, integration in AVAILABLE_INTEGRATIONS.items():
        try:
            hook_func = getattr(integration, f'uninstall_{name}_hooks')
            hook_func()
        except Exception as e:
            print(f"Failed to uninstall {name} hooks: {e}")


def register_memori_instance(memori_instance):
    """Register a Memori instance with all integrations"""
    for integration in AVAILABLE_INTEGRATIONS.values():
        try:
            integration.register_memori_instance(memori_instance)
        except Exception as e:
            print(f"Failed to register instance with integration: {e}")


def unregister_memori_instance(memori_instance):
    """Unregister a Memori instance from all integrations"""
    for integration in AVAILABLE_INTEGRATIONS.values():
        try:
            integration.unregister_memori_instance(memori_instance)
        except Exception as e:
            print(f"Failed to unregister instance from integration: {e}")


def get_integration_stats() -> List[Dict[str, Any]]:
    """Get statistics from all integrations"""
    stats = []
    for integration in AVAILABLE_INTEGRATIONS.values():
        try:
            stats.append(integration.get_stats())
        except Exception as e:
            print(f"Failed to get stats from integration: {e}")
    return stats
