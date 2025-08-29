#!/usr/bin/env python3
"""
Debug what the interceptor is actually injecting
"""

import asyncio
from memori import Memori

async def debug_interceptor():
    """Debug what the interceptor injects"""
    print("=== Debugging Interceptor Context Injection ===\n")
    
    # Initialize the same way as litellm_test.py
    litellm_memory = Memori(
        database_connect="sqlite:///patch-4.db",
        conscious_ingest=True,
        verbose=True,
    )
    litellm_memory.enable()
    await asyncio.sleep(2)
    
    # Test what the interceptor would inject
    print("🔍 Testing what gets injected via interceptor...")
    
    # Simulate the _inject_litellm_context call that happens in the interceptor
    test_params = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": "what is my name"
            }
        ]
    }
    
    print("BEFORE interceptor injection:")
    for i, msg in enumerate(test_params["messages"]):
        print(f"  Message {i}: {msg}")
    
    # This is what the interceptor does
    injected_params = litellm_memory._inject_litellm_context(test_params.copy(), mode="conscious")
    
    print(f"\nAFTER interceptor injection:")
    for i, msg in enumerate(injected_params["messages"]):
        print(f"  Message {i}:")
        print(f"    Role: {msg['role']}")
        if msg['role'] == 'system':
            print(f"    Content (full): {repr(msg['content'])}")
        else:
            print(f"    Content: {msg['content']}")
    
    print(f"\n🧠 Context injection flag: {litellm_memory._conscious_context_injected}")

if __name__ == "__main__":
    asyncio.run(debug_interceptor())