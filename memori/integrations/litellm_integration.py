"""
LiteLLM Integration - DEPRECATED

This integration is deprecated. LiteLLM now uses native callbacks
implemented directly in memori/core/memory.py

The native callback system is more robust and uses LiteLLM's official
extension mechanism instead of monkey-patching.

Use: memori.enable() which registers with LiteLLM's success_callback system.
"""
