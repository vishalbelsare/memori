"""
Universal LLM Integration - Plug-and-Play Memory Recording

🎯 SIMPLE USAGE (RECOMMENDED):
Just call memori.enable() and use ANY LLM library normally!

```python
from memoriai import Memori

memori = Memori(...)
memori.enable()  # 🎉 That's it! 

# Now use ANY LLM library normally - all calls will be auto-recorded:

# LiteLLM (native callbacks)
from litellm import completion
completion(model="gpt-4o", messages=[...])  # ✅ Auto-recorded

# Direct OpenAI (auto-wrapping)
import openai
client = openai.OpenAI(api_key="...")
client.chat.completions.create(...)  # ✅ Auto-recorded  

# Direct Anthropic (auto-wrapping)  
import anthropic
client = anthropic.Anthropic(api_key="...")
client.messages.create(...)  # ✅ Auto-recorded
```

The universal system automatically detects and records ALL LLM providers
without requiring wrapper classes or complex setup.
"""

from typing import Any, Dict, List
from loguru import logger

# Legacy imports (all deprecated)
from . import anthropic_integration, litellm_integration, openai_integration

__all__ = [
    # Legacy functions (deprecated - use memori.enable() instead)
    "install_all_hooks",
    "uninstall_all_hooks", 
    "register_memori_instance",
    "unregister_memori_instance",
    "get_integration_stats",
]


# ALL FUNCTIONS BELOW ARE DEPRECATED
# Use memori.enable() for universal auto-recording instead

def install_all_hooks():
    """DEPRECATED: Use memori.enable() for universal auto-recording"""
    logger.warning(
        "🚨 install_all_hooks() is deprecated!\n"
        "✅ NEW SIMPLE WAY: Just call memori.enable()\n"
        "   This automatically handles ALL providers (LiteLLM, OpenAI, Anthropic, etc.)"
    )


def uninstall_all_hooks():
    """DEPRECATED: Use memori.disable() instead"""
    logger.warning(
        "🚨 uninstall_all_hooks() is deprecated!\n"
        "✅ NEW SIMPLE WAY: Just call memori.disable()"
    )


def register_memori_instance(memori_instance):
    """DEPRECATED: Use memori.enable() instead"""
    logger.warning(
        "🚨 register_memori_instance() is deprecated!\n"
        "✅ NEW SIMPLE WAY: memori.enable() automatically handles registration"
    )


def unregister_memori_instance(memori_instance):
    """DEPRECATED: Use memori.disable() instead"""
    logger.warning(
        "🚨 unregister_memori_instance() is deprecated!\n"
        "✅ NEW SIMPLE WAY: memori.disable() automatically handles cleanup"
    )


def get_integration_stats() -> List[Dict[str, Any]]:
    """DEPRECATED: Use memori.get_integration_stats() instead"""
    logger.warning(
        "🚨 get_integration_stats() is deprecated!\n"
        "✅ NEW WAY: Use memori.get_integration_stats() for universal stats"
    )
    return []


# Migration guide for existing users
def show_migration_guide():
    """Show migration guide for users upgrading to universal system"""
    print("""
🚀 MEMORI UNIVERSAL INTEGRATION - MIGRATION GUIDE

OLD WAY (deprecated):
    from memoriai.integrations import install_all_hooks, register_memori_instance
    install_all_hooks()
    register_memori_instance(memori)

NEW WAY (simple):
    memori.enable()  # That's it! Works with ALL providers automatically
    
🎯 BENEFITS:
✅ No complex setup - one line enables everything
✅ Auto-detects all LLM providers (LiteLLM, OpenAI, Anthropic, etc.)
✅ No wrapper classes needed - use libraries normally
✅ Safer - no monkey-patching, uses official extension APIs
✅ Future-proof - automatically supports new providers
    """)


# For backward compatibility, provide simple passthrough
try:
    from .openai_integration import MemoriOpenAI
    from .anthropic_integration import MemoriAnthropic
    
    # But warn users about the better way
    def __getattr__(name):
        if name in ["MemoriOpenAI", "MemoriAnthropic"]:
            logger.warning(
                f"🚨 {name} wrapper classes are deprecated!\n"
                f"✅ NEW SIMPLE WAY: Use memori.enable() and import {name.replace('Memori', '').lower()} normally"
            )
            if name == "MemoriOpenAI":
                return MemoriOpenAI
            elif name == "MemoriAnthropic": 
                return MemoriAnthropic
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
        
except ImportError:
    # Wrapper classes not available, that's fine
    pass
