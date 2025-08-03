"""
LiteLLM Integration - Automatic conversation recording for LiteLLM API calls
"""

from typing import Any, Dict

from loguru import logger

# Global registry for Memori instances
_memori_instances = []
_original_litellm_functions = {}
_hooks_installed = False


def install_litellm_hooks():
    """Install hooks to intercept LiteLLM API calls"""
    global _hooks_installed, _original_litellm_functions

    if _hooks_installed:
        return

    try:
        import litellm

        # Store original functions
        _original_litellm_functions["completion"] = litellm.completion
        _original_litellm_functions["acompletion"] = getattr(
            litellm, "acompletion", None
        )

        # Replace with our wrapped versions
        litellm.completion = _wrapped_completion
        if _original_litellm_functions["acompletion"]:
            litellm.acompletion = _wrapped_acompletion

        _hooks_installed = True
        logger.info("LiteLLM hooks installed for auto-recording")

    except ImportError:
        logger.warning("LiteLLM not installed, cannot install hooks")
    except Exception as e:
        logger.error(f"Failed to install LiteLLM hooks: {e}")


def uninstall_litellm_hooks():
    """Uninstall LiteLLM hooks and restore original functions"""
    global _hooks_installed, _original_litellm_functions

    if not _hooks_installed:
        return

    try:
        import litellm

        # Restore original functions
        if "completion" in _original_litellm_functions:
            litellm.completion = _original_litellm_functions["completion"]

        if (
            "acompletion" in _original_litellm_functions
            and _original_litellm_functions["acompletion"]
        ):
            litellm.acompletion = _original_litellm_functions["acompletion"]

        _hooks_installed = False
        _original_litellm_functions.clear()
        logger.info("LiteLLM hooks uninstalled")

    except ImportError:
        logger.warning("LiteLLM not available for hook uninstallation")
    except Exception as e:
        logger.error(f"Failed to uninstall LiteLLM hooks: {e}")


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


def _wrapped_completion(**kwargs):
    """Wrapped version of LiteLLM completion"""
    # Call original function
    response = _original_litellm_functions["completion"](**kwargs)

    # Record conversation for all active Memori instances
    _record_litellm_conversation(kwargs, response)

    return response


async def _wrapped_acompletion(**kwargs):
    """Wrapped version of LiteLLM async completion"""
    # Call original function
    response = await _original_litellm_functions["acompletion"](**kwargs)

    # Record conversation for all active Memori instances
    _record_litellm_conversation(kwargs, response)

    return response


def _record_litellm_conversation(request_kwargs: Dict[str, Any], response):
    """Record a LiteLLM conversation"""
    global _memori_instances

    try:
        # Extract conversation details
        messages = request_kwargs.get("messages", [])
        model = request_kwargs.get("model", "unknown")

        # Find user input (last user message)
        user_input = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                user_input = message.get("content", "")
                break

        # Extract AI response
        ai_output = ""
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            if hasattr(choice, "message") and choice.message:
                ai_output = choice.message.content or ""

        # Calculate tokens used
        tokens_used = 0
        if hasattr(response, "usage") and response.usage:
            tokens_used = getattr(response.usage, "total_tokens", 0)

        # Record for all active instances
        for memori_instance in _memori_instances:
            if memori_instance.is_enabled:
                try:
                    memori_instance.record_conversation(
                        user_input=user_input,
                        ai_output=ai_output,
                        model=model,
                        metadata={
                            "integration": "litellm",
                            "api_type": "completion",
                            "tokens_used": tokens_used,
                            "auto_recorded": True,
                            "provider": _extract_provider_from_model(model),
                        },
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to record conversation for instance {memori_instance.namespace}: {e}"
                    )

    except Exception as e:
        logger.error(f"Failed to record LiteLLM conversation: {e}")


def _extract_provider_from_model(model: str) -> str:
    """Extract provider from model name"""
    if not model:
        return "unknown"

    # Common provider prefixes in LiteLLM
    if model.startswith("gpt"):
        return "openai"
    elif model.startswith("claude"):
        return "anthropic"
    elif model.startswith("gemini"):
        return "google"
    elif model.startswith("command"):
        return "cohere"
    elif "/" in model:
        return model.split("/")[0]
    else:
        return "unknown"


def get_stats() -> Dict[str, Any]:
    """Get integration statistics"""
    return {
        "integration": "litellm",
        "hooks_installed": _hooks_installed,
        "active_instances": len(_memori_instances),
        "instance_namespaces": [instance.namespace for instance in _memori_instances],
    }
