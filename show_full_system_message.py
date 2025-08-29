#!/usr/bin/env python3
"""
Show the complete system message being sent
"""

import asyncio
from memori import Memori

async def show_full_system_message():
    """Show the complete system message"""
    print("=== Full System Message ===\n")
    
    # Initialize Memori
    memori = Memori(
        database_connect="sqlite:///patch-4.db",
        namespace="default",
        conscious_ingest=True,
        auto_ingest=False
    )
    
    memori.enable()
    await asyncio.sleep(2)
    
    # Inject context
    test_params = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "What is my name?"}
        ]
    }
    
    injected_params = memori._inject_litellm_context(test_params.copy(), mode="conscious")
    
    # Find and show the complete system message
    for msg in injected_params["messages"]:
        if msg["role"] == "system":
            print("COMPLETE SYSTEM MESSAGE:")
            print("=" * 80)
            print(msg["content"])
            print("=" * 80)
            print(f"Length: {len(msg['content'])} characters")
            break

if __name__ == "__main__":
    asyncio.run(show_full_system_message())