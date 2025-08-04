"""
Universal LLM Integration - Plug-and-Play Memory Recording

🎯 SIMPLE USAGE (RECOMMENDED):
Just call memori.enable() and use ANY LLM library normally!

```python
from memori import Memori

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
    # Wrapper classes for direct SDK usage
    "MemoriOpenAI",
    "MemoriAnthropic",
]


# For backward compatibility, provide simple passthrough
try:
    from .anthropic_integration import MemoriAnthropic
    from .openai_integration import MemoriOpenAI

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
