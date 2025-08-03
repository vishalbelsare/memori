"""
LiteLLM Integration - DEPRECATED

This integration is deprecated. LiteLLM now uses native callbacks 
implemented directly in memoriai/core/memory.py

The native callback system is more robust and uses LiteLLM's official
extension mechanism instead of monkey-patching.

Use: memori.enable() which registers with LiteLLM's success_callback system.
"""

from typing import Any, Dict
from loguru import logger

def install_litellm_hooks():
    """DEPRECATED: Use memori.enable() instead which uses native LiteLLM callbacks"""
    logger.warning(
        "install_litellm_hooks() is deprecated. "
        "Use memori.enable() which implements native LiteLLM callbacks."
    )

def uninstall_litellm_hooks():
    """DEPRECATED: Use memori.disable() instead"""
    logger.warning(
        "uninstall_litellm_hooks() is deprecated. "
        "Use memori.disable() which properly unregisters native callbacks."
    )

def register_memori_instance(memori_instance):
    """DEPRECATED: No longer needed with native callback system"""
    logger.warning(
        "register_memori_instance() is deprecated. "
        "Use memori.enable() to register with LiteLLM's native callback system."
    )

def unregister_memori_instance(memori_instance):
    """DEPRECATED: No longer needed with native callback system"""
    logger.warning(
        "unregister_memori_instance() is deprecated. "
        "Use memori.disable() to unregister from LiteLLM's native callback system."
    )

def get_stats() -> Dict[str, Any]:
    """Get integration statistics - DEPRECATED"""
    logger.warning(
        "litellm_integration.get_stats() is deprecated. "
        "Use memori.get_integration_stats() instead."
    )
    return {
        "integration": "litellm_deprecated",
        "status": "deprecated",
        "message": "Use native callback system in memory.py",
        "hooks_installed": False,
        "active_instances": 0,
    }
