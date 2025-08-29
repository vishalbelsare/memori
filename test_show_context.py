#!/usr/bin/env python3
"""
Show the full conscious context that gets injected
"""

import asyncio
from memori import Memori

async def show_conscious_context():
    """Show the full conscious context"""
    print("=== Conscious Context Full Display ===\n")
    
    # Initialize Memori with conscious_ingest=True
    memori = Memori(
        database_connect="sqlite:///patch-4.db",
        namespace="default", 
        conscious_ingest=True,
        auto_ingest=False
    )
    
    memori.enable()
    await asyncio.sleep(2)  # Wait for initialization
    
    # Test context injection
    test_params = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello, tell me about myself based on what you know."}
        ]
    }
    
    injected_params = memori._inject_litellm_context(test_params.copy(), mode="conscious")
    
    # Show the full system message
    for msg in injected_params.get("messages", []):
        if msg.get("role") == "system":
            print("📋 FULL CONSCIOUS CONTEXT:")
            print("=" * 80)
            print(msg.get("content", ""))
            print("=" * 80)
            print(f"Context length: {len(msg.get('content', ''))} characters")
            break

if __name__ == "__main__":
    asyncio.run(show_conscious_context())