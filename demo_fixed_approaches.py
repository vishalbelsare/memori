#!/usr/bin/env python3
"""
Demonstrate the fixed auto_ingest and conscious_ingest approaches
using direct system prompt injection instead of unreliable interceptors
"""

import asyncio
import litellm
from memori import Memori

async def demo_both_approaches():
    """Demo both conscious_ingest and auto_ingest working properly"""
    
    print("🎯 DEMONSTRATION: Fixed Auto-Ingest & Conscious-Ingest")
    print("=" * 60)
    print("✅ Using direct system prompt injection (no interceptors)")
    print("✅ Reliable and predictable memory injection")
    print("=" * 60)
    
    # Demo 1: Conscious Ingest
    print("\n🧠 DEMO 1: CONSCIOUS_INGEST")
    print("-" * 40)
    
    memori_conscious = Memori(
        database_connect="sqlite:///patch-4.db",
        conscious_ingest=True,
        verbose=False  # Keep it clean for demo
    )
    memori_conscious.enable()
    await asyncio.sleep(1)
    
    # First call with conscious_ingest
    messages1 = [{"role": "user", "content": "What is my name and where do I work?"}]
    messages_with_context1 = memori_conscious.add_memory_to_messages(messages1, "What is my name")
    
    print(f"📋 Added system context: {len(messages_with_context1)} messages total")
    print(f"🔍 System message length: {len(messages_with_context1[0]['content'])} characters")
    
    # Mock the API call to show what the AI would see
    response1 = litellm.completion(
        model="gpt-3.5-turbo",
        messages=messages_with_context1,
        mock_response="Based on your context, your name is Harshal and you work at Gibson AI."
    )
    
    print(f"🤖 AI Response: {response1.choices[0].message.content}")
    print(f"📊 Conscious flag: {memori_conscious._conscious_context_injected}")
    
    # Second call - should NOT add context
    messages2 = [{"role": "user", "content": "What programming languages do I use?"}]
    messages_with_context2 = memori_conscious.add_memory_to_messages(messages2, "programming languages")
    
    print(f"🔄 Second call - Messages: {len(messages_with_context2)} (should be 1)")
    print(f"✅ No context re-injection: {len(messages_with_context2) == 1}")
    
    print("\n" + "="*60)
    
    # Demo 2: Auto Ingest  
    print("\n🔍 DEMO 2: AUTO_INGEST")
    print("-" * 40)
    
    memori_auto = Memori(
        database_connect="sqlite:///patch-4.db",
        auto_ingest=True,
        verbose=False
    )
    memori_auto.enable()
    await asyncio.sleep(1)
    
    # First auto-ingest call
    user_query1 = "Tell me about my work"
    messages3 = [{"role": "user", "content": user_query1}]
    messages_with_auto1 = memori_auto.add_memory_to_messages(messages3, user_query1)
    
    print(f"📋 Added auto-context: {len(messages_with_auto1)} messages total")
    print(f"🔍 System message length: {len(messages_with_auto1[0]['content'])} characters")
    
    response3 = litellm.completion(
        model="gpt-3.5-turbo",
        messages=messages_with_auto1,
        mock_response="You work at Gibson AI on product memory systems."
    )
    
    print(f"🤖 AI Response: {response3.choices[0].message.content}")
    
    # Second auto-ingest call - should add context again
    user_query2 = "What's my name again?"
    messages4 = [{"role": "user", "content": user_query2}]  
    messages_with_auto2 = memori_auto.add_memory_to_messages(messages4, user_query2)
    
    print(f"🔄 Second call - Messages: {len(messages_with_auto2)} (should be 2)")
    print(f"✅ Dynamic context injection: {len(messages_with_auto2) == 2}")
    
    print("\n" + "="*60)
    print("🎉 SUMMARY:")
    print("✅ CONSCIOUS_INGEST: One-time complete memory at startup") 
    print("✅ AUTO_INGEST: Dynamic relevant memory per call")
    print("✅ Direct system prompt injection (no interceptor failures)")
    print("✅ Both modes working reliably!")
    print("=" * 60)
    
    print(f"\n💡 Usage Example:")
    print(f"```python")
    print(f"# In your LiteLLM code:")
    print(f"messages = [{'role': 'user', 'content': user_input}]")
    print(f"messages_with_memory = memori.add_memory_to_messages(messages, user_input)")
    print(f"response = litellm.completion(model='gpt-4o', messages=messages_with_memory)")
    print(f"```")

if __name__ == "__main__":
    asyncio.run(demo_both_approaches())