#!/usr/bin/env python3
"""
Test conscious_ingest context injection feature

This test verifies that:
1. conscious_ingest=True copies conscious-info memories to short-term memory
2. conscious_ingest=True injects ALL short-term memory summaries as initial context
3. Context is only injected once at startup (different from auto_ingest)
"""

import asyncio
import sys
from memori import Memori

async def test_conscious_ingest_context_injection():
    """Test conscious context injection functionality"""
    print("=== Testing Conscious Ingest Context Injection ===\n")
    
    # Initialize Memori with conscious_ingest=True
    memori = Memori(
        database_connect="sqlite:///patch-4.db",
        namespace="default",
        conscious_ingest=True,  # This should inject all short-term memory as initial context
        auto_ingest=False       # Ensure auto_ingest is off for this test
    )
    
    # Enable Memori 
    memori.enable()
    print("✅ Memori enabled with conscious_ingest=True")
    
    # Wait a moment for conscious agent initialization
    await asyncio.sleep(2)
    
    # Check short-term memory contents
    print("\n--- Short-Term Memory Contents ---")
    context = memori._get_conscious_context()
    print(f"Found {len(context)} items in short-term memory:")
    
    for i, item in enumerate(context, 1):
        summary = item.get('summary', '')[:100]
        category = item.get('category_primary', 'unknown')
        print(f"  {i}. [{category.upper()}] {summary}...")
    
    # Test context injection flag state
    print(f"\n--- Context Injection State ---")
    print(f"conscious_context_injected: {memori._conscious_context_injected}")
    print(f"conscious_ingest: {memori.conscious_ingest}")
    print(f"auto_ingest: {memori.auto_ingest}")
    
    # Simulate LiteLLM context injection 
    print(f"\n--- Testing Context Injection ---")
    
    # First call - should inject context
    test_params_1 = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello, what do you know about me?"}
        ]
    }
    
    print("🔄 First LLM call (should inject all short-term memory):")
    injected_params_1 = memori._inject_litellm_context(test_params_1.copy(), mode="conscious")
    
    # Check if context was injected
    system_message = None
    for msg in injected_params_1.get("messages", []):
        if msg.get("role") == "system":
            system_message = msg.get("content", "")
            break
    
    if system_message:
        print(f"✅ Context injected! System message length: {len(system_message)} characters")
        print("📋 System message preview:")
        print(system_message[:300] + "..." if len(system_message) > 300 else system_message)
    else:
        print("❌ No system message found!")
    
    print(f"📊 Context injection flag after first call: {memori._conscious_context_injected}")
    
    # Second call - should NOT inject context again
    test_params_2 = {
        "model": "gpt-4", 
        "messages": [
            {"role": "user", "content": "What's my name again?"}
        ]
    }
    
    print("\n🔄 Second LLM call (should NOT inject context again):")
    injected_params_2 = memori._inject_litellm_context(test_params_2.copy(), mode="conscious")
    
    # Check if context was NOT injected
    system_message_2 = None
    for msg in injected_params_2.get("messages", []):
        if msg.get("role") == "system":
            system_message_2 = msg.get("content", "")
            break
    
    if not system_message_2:
        print("✅ No context injected on second call (as expected)")
    else:
        print(f"❌ Context was unexpectedly injected again! Length: {len(system_message_2)}")
    
    print(f"📊 Context injection flag after second call: {memori._conscious_context_injected}")
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"✅ Short-term memory items: {len(context)}")
    print(f"✅ First call context injection: {'SUCCESS' if system_message else 'FAILED'}")
    print(f"✅ Second call no injection: {'SUCCESS' if not system_message_2 else 'FAILED'}")
    print(f"✅ Conscious context flag management: {'SUCCESS' if memori._conscious_context_injected else 'FAILED'}")
    
    # Comparison with auto_ingest behavior
    print(f"\n=== Comparison: Auto Ingest vs Conscious Ingest ===")
    print("🔄 Testing auto_ingest mode (for comparison):")
    
    # Reset flag for comparison
    memori._conscious_context_injected = False
    auto_params = memori._inject_litellm_context(test_params_1.copy(), mode="auto") 
    
    auto_system_message = None
    for msg in auto_params.get("messages", []):
        if msg.get("role") == "system":
            auto_system_message = msg.get("content", "")
            break
    
    print(f"📊 Auto-ingest context length: {len(auto_system_message) if auto_system_message else 0}")
    print(f"📊 Conscious-ingest context length: {len(system_message) if system_message else 0}")
    
    if system_message and auto_system_message:
        print(f"📊 Conscious context is {len(system_message)/len(auto_system_message):.1f}x larger than auto context")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_conscious_ingest_context_injection())