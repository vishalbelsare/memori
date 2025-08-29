#!/usr/bin/env python3
"""
Debug what's actually being sent to the LLM
"""

import asyncio
from memori import Memori

async def debug_context_injection():
    """Debug the actual content being injected"""
    print("=== Debugging Context Injection ===\n")
    
    # Initialize Memori
    memori = Memori(
        database_connect="sqlite:///patch-4.db",
        namespace="default",
        conscious_ingest=True,
        auto_ingest=False
    )
    
    memori.enable()
    await asyncio.sleep(2)
    
    # Simulate what happens in LiteLLM injection
    test_params = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "What is my name?"}
        ]
    }
    
    print("BEFORE injection:")
    print("Messages:", test_params["messages"])
    print()
    
    # Inject context
    injected_params = memori._inject_litellm_context(test_params.copy(), mode="conscious")
    
    print("AFTER injection:")
    for i, msg in enumerate(injected_params["messages"]):
        print(f"Message {i}:")
        print(f"  Role: {msg['role']}")
        print(f"  Content: {msg['content'][:200]}..." if len(msg['content']) > 200 else f"  Content: {msg['content']}")
        print()
    
    # Also check the conscious context directly
    print("CONSCIOUS CONTEXT DIRECT:")
    context = memori._get_conscious_context()
    print(f"Retrieved {len(context)} items:")
    for i, item in enumerate(context[:10]):  # Show first 10
        print(f"  {i+1}. [{item.get('category_primary', 'UNKNOWN')}] {item.get('searchable_content', item.get('summary', ''))}")

if __name__ == "__main__":
    asyncio.run(debug_context_injection())