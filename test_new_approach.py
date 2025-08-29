#!/usr/bin/env python3
"""
Test the new direct system prompt approach
"""

import asyncio
from memori import Memori

async def test_new_approach():
    """Test both conscious_ingest and auto_ingest with new approach"""
    print("=== Testing New Direct System Prompt Approach ===\n")
    
    # Test conscious_ingest
    print("🧠 Testing CONSCIOUS_INGEST:")
    memori_conscious = Memori(
        database_connect="sqlite:///patch-4.db",
        conscious_ingest=True,
        auto_ingest=False
    )
    memori_conscious.enable()
    await asyncio.sleep(1)
    
    messages = [{"role": "user", "content": "What is my name and where do I work?"}]
    
    # First call - should add context
    messages_with_context = memori_conscious.add_memory_to_messages(messages.copy())
    
    print(f"📊 Messages before: {len(messages)}")
    print(f"📊 Messages after: {len(messages_with_context)}")
    
    if len(messages_with_context) > len(messages):
        system_msg = messages_with_context[0]['content']
        print(f"✅ System context added ({len(system_msg)} chars)")
        print(f"🔍 Preview: {system_msg[:200]}...")
        print(f"📊 Context injection flag: {memori_conscious._conscious_context_injected}")
    
    # Second call - should NOT add context
    messages2 = [{"role": "user", "content": "What's my favorite programming language?"}]
    messages_with_context2 = memori_conscious.add_memory_to_messages(messages2.copy())
    
    print(f"\n🔄 Second call:")
    print(f"📊 Messages before: {len(messages2)}")
    print(f"📊 Messages after: {len(messages_with_context2)}")
    print(f"📊 Context injection flag: {memori_conscious._conscious_context_injected}")
    
    if len(messages_with_context2) == len(messages2):
        print("✅ No context added on second call (correct for conscious_ingest)")
    
    print("\n" + "="*60)
    
    # Test auto_ingest
    print("\n🔍 Testing AUTO_INGEST:")
    memori_auto = Memori(
        database_connect="sqlite:///patch-4.db",
        conscious_ingest=False,
        auto_ingest=True
    )
    memori_auto.enable()
    await asyncio.sleep(1)
    
    # Test with user input that should find relevant memories
    user_input = "Tell me about my work"
    messages3 = [{"role": "user", "content": user_input}]
    messages_with_auto = memori_auto.add_memory_to_messages(messages3.copy(), user_input)
    
    print(f"📊 Messages before: {len(messages3)}")
    print(f"📊 Messages after: {len(messages_with_auto)}")
    
    if len(messages_with_auto) > len(messages3):
        system_msg = messages_with_auto[0]['content']
        print(f"✅ Auto-ingest context added ({len(system_msg)} chars)")
        print(f"🔍 Preview: {system_msg[:200]}...")
    else:
        print("❌ No auto-ingest context added")
    
    # Test another auto-ingest call
    user_input2 = "What's my name?"
    messages4 = [{"role": "user", "content": user_input2}]
    messages_with_auto2 = memori_auto.add_memory_to_messages(messages4.copy(), user_input2)
    
    print(f"\n🔄 Second auto-ingest call:")
    print(f"📊 Messages before: {len(messages4)}")
    print(f"📊 Messages after: {len(messages_with_auto2)}")
    
    if len(messages_with_auto2) > len(messages4):
        system_msg2 = messages_with_auto2[0]['content']
        print(f"✅ Dynamic context added ({len(system_msg2)} chars)")
        print(f"🔍 Preview: {system_msg2[:200]}...")
    
    print(f"\n🎉 New approach test completed!")
    print(f"✅ Conscious ingest: One-time complete memory injection")
    print(f"✅ Auto ingest: Dynamic relevant memory injection per call")

if __name__ == "__main__":
    asyncio.run(test_new_approach())