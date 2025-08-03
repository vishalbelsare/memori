"""
Anthropic Integration - Automatic conversation recording for Anthropic API calls
"""

from typing import Any, Dict

from loguru import logger

# Global registry for Memori instances
_memori_instances = []
_original_anthropic_functions = {}
_hooks_installed = False


def install_anthropic_hooks():
    """Install hooks to intercept Anthropic API calls"""
    global _hooks_installed, _original_anthropic_functions

    if _hooks_installed:
        return

    try:
        import anthropic

        # Store original functions
        _original_anthropic_functions["messages_create"] = (
            anthropic.resources.messages.Messages.create
        )

        # Replace with our wrapped versions
        anthropic.resources.messages.Messages.create = _wrapped_messages_create

        _hooks_installed = True
        logger.info("Anthropic hooks installed for auto-recording")

    except ImportError:
        logger.warning("Anthropic not installed, cannot install hooks")
    except Exception as e:
        logger.error(f"Failed to install Anthropic hooks: {e}")


def uninstall_anthropic_hooks():
    """Uninstall Anthropic hooks and restore original functions"""
    global _hooks_installed, _original_anthropic_functions

    if not _hooks_installed:
        return

    try:
        import anthropic

        # Restore original functions
        if "messages_create" in _original_anthropic_functions:
            anthropic.resources.messages.Messages.create = (
                _original_anthropic_functions["messages_create"]
            )

        _hooks_installed = False
        _original_anthropic_functions.clear()
        logger.info("Anthropic hooks uninstalled")

    except ImportError:
        logger.warning("Anthropic not available for hook uninstallation")
    except Exception as e:
        logger.error(f"Failed to uninstall Anthropic hooks: {e}")


def register_memori_instance(memori_instance):
    """Register a Memori instance for auto-recording"""
    global _memori_instances
    if memori_instance not in _memori_instances:
        _memori_instances.append(memori_instance)
        logger.debug(f"Registered Memori instance: {memori_instance.namespace}")


def unregister_memori_instance(memori_instance):
    """Unregister a Memori instance"""
    global _memori_instances
    if memori_instance in _memori_instances:
        _memori_instances.remove(memori_instance)
        logger.debug(f"Unregistered Memori instance: {memori_instance.namespace}")


def _wrapped_messages_create(self, **kwargs):
    """Wrapped version of Anthropic messages create"""
    # Call original function
    response = _original_anthropic_functions["messages_create"](self, **kwargs)

    # Record conversation for all active Memori instances
    _record_anthropic_conversation(kwargs, response)

    return response


def _record_anthropic_conversation(request_kwargs: Dict[str, Any], response):
    """Record an Anthropic conversation"""
    global _memori_instances

    try:
        # Extract conversation details
        messages = request_kwargs.get("messages", [])
        model = request_kwargs.get("model", "claude-unknown")

        # Find user input (last user message)
        user_input = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                content = message.get("content", "")
                if isinstance(content, list):
                    # Handle content blocks
                    user_input = " ".join(
                        [
                            block.get("text", "")
                            for block in content
                            if isinstance(block, dict) and block.get("type") == "text"
                        ]
                    )
                else:
                    user_input = content
                break

        # Extract AI response
        ai_output = ""
        if hasattr(response, "content") and response.content:
            if isinstance(response.content, list):
                # Handle content blocks
                ai_output = " ".join(
                    [block.text for block in response.content if hasattr(block, "text")]
                )
            else:
                ai_output = str(response.content)

        # Calculate tokens used
        tokens_used = 0
        if hasattr(response, "usage") and response.usage:
            input_tokens = getattr(response.usage, "input_tokens", 0)
            output_tokens = getattr(response.usage, "output_tokens", 0)
            tokens_used = input_tokens + output_tokens

        # Record for all active instances
        for memori_instance in _memori_instances:
            if memori_instance.is_enabled:
                try:
                    memori_instance.record_conversation(
                        user_input=user_input,
                        ai_output=ai_output,
                        model=model,
                        metadata={
                            "integration": "anthropic",
                            "api_type": "messages",
                            "tokens_used": tokens_used,
                            "auto_recorded": True,
                        },
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to record conversation for instance {memori_instance.namespace}: {e}"
                    )

    except Exception as e:
        logger.error(f"Failed to record Anthropic conversation: {e}")


def get_stats() -> Dict[str, Any]:
    """Get integration statistics"""
    return {
        "integration": "anthropic",
        "hooks_installed": _hooks_installed,
        "active_instances": len(_memori_instances),
        "instance_namespaces": [instance.namespace for instance in _memori_instances],
    }
