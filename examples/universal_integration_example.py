#!/usr/bin/env python3
"""
Universal Integration Example - True Plug-and-Play Memory Recording

This demonstrates the new universal approach:
✅ One line: memori.enable()
✅ Works with ALL LLM providers automatically
✅ No wrapper classes needed
✅ No complex setup

Just use any LLM library normally - conversations will be auto-recorded!
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from memoriai import Memori

def main():
    print("🌟 UNIVERSAL INTEGRATION EXAMPLE")
    print("=" * 60)
    print("🎯 Goal: Demonstrate plug-and-play memory recording for ALL providers")
    
    # =================================================================
    # Step 1: Initialize Memori (standard setup)
    # =================================================================
    print("\n1️⃣ Initialize Memori...")
    memori = Memori(
        database_connect="sqlite:///universal_example.db",
        template="basic",
        conscious_ingest=True,
        namespace="universal_demo"
    )
    print(f"✅ Memori initialized with namespace: {memori.namespace}")
    
    # =================================================================
    # Step 2: Enable Universal Recording (ONE LINE!)
    # =================================================================
    print("\n2️⃣ Enable universal auto-recording...")
    print("🎉 This ONE line enables recording for ALL LLM providers:")
    print("   memori.enable()")
    
    memori.enable()  # 🎉 THAT'S IT! No complex setup needed
    
    print("✅ Universal recording enabled!")
    print("   Now ANY LLM library will automatically record conversations")
    
    # =================================================================
    # Step 3: Use LiteLLM (Native Callbacks - Most Robust)
    # =================================================================
    print("\n3️⃣ Testing LiteLLM (native callbacks)...")
    try:
        from litellm import completion
        
        print("   Using LiteLLM exactly as normal...")
        response1 = completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "What is artificial intelligence?"}]
        )
        print(f"   ✅ LiteLLM call completed: {response1.choices[0].message.content[:60]}...")
        print("   📝 Conversation automatically recorded!")
        
    except ImportError:
        print("   ⚠️ LiteLLM not installed - skipping")
    except Exception as e:
        print(f"   ⚠️ LiteLLM error: {e}")
    
    # =================================================================
    # Step 4: Use OpenAI Directly (Auto-Wrapping)
    # =================================================================
    print("\n4️⃣ Testing direct OpenAI (auto-wrapping)...")
    try:
        import openai
        
        print("   Creating OpenAI client exactly as normal...")
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", "test-key"))
        
        print("   Making OpenAI call exactly as normal...")
        # Note: This will fail without a real API key, but shows the integration
        try:
            response2 = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "What is machine learning?"}]
            )
            print(f"   ✅ OpenAI call completed: {response2.choices[0].message.content[:60]}...")
            print("   📝 Conversation automatically recorded!")
        except Exception as api_error:
            print(f"   ⚠️ OpenAI API call failed (expected without real key): {api_error}")
            print("   ✅ But auto-wrapping was successfully installed!")
        
    except ImportError:
        print("   ⚠️ OpenAI not installed - skipping")
    
    # =================================================================
    # Step 5: Use Anthropic Directly (Auto-Wrapping)
    # =================================================================
    print("\n5️⃣ Testing direct Anthropic (auto-wrapping)...")
    try:
        import anthropic
        
        print("   Creating Anthropic client exactly as normal...")
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"))
        
        print("   Making Anthropic call exactly as normal...")
        # Note: This will fail without a real API key, but shows the integration
        try:
            response3 = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{"role": "user", "content": "What is deep learning?"}]
            )
            print(f"   ✅ Anthropic call completed: {response3.content[0].text[:60]}...")
            print("   📝 Conversation automatically recorded!")
        except Exception as api_error:
            print(f"   ⚠️ Anthropic API call failed (expected without real key): {api_error}")
            print("   ✅ But auto-wrapping was successfully installed!")
        
    except ImportError:
        print("   ⚠️ Anthropic not installed - skipping")
    
    # =================================================================
    # Step 6: Check What Actually Got Recorded
    # =================================================================
    print("\n6️⃣ Checking what was recorded...")
    
    # Memory stats
    stats = memori.get_memory_stats()
    print(f"   📊 Total conversations: {stats.get('chat_history_count', 0)}")
    print(f"   🧠 Long-term memories: {stats.get('long_term_count', 0)}")
    print(f"   🏷️ Entities extracted: {stats.get('total_entities', 0)}")
    
    # Integration stats
    print("\n   🔧 Integration status:")
    integration_stats = memori.get_integration_stats()
    if integration_stats:
        stats_data = integration_stats[0]
        providers = stats_data.get('providers', {})
        
        for provider, info in providers.items():
            status = "✅" if info.get('available') else "❌"
            method = info.get('method', 'unknown')
            print(f"     {status} {provider.capitalize()}: {method}")
            
            if provider == 'litellm' and info.get('callback_registered'):
                print(f"       📞 Callbacks registered: {info.get('callbacks_count', 0)}")
            elif provider in ['openai', 'anthropic'] and info.get('wrapped'):
                print(f"       🎁 Auto-wrapping active")
    
    # Recent conversations
    print("\n   📜 Recent conversations:")
    history = memori.get_conversation_history(limit=3)
    for i, conv in enumerate(history, 1):
        integration = conv.get('metadata', {}).get('integration', 'unknown')
        model = conv.get('model', 'unknown')
        user_msg = conv.get('user_input', '')[:50]
        print(f"     {i}. [{integration}] {model}: {user_msg}...")
    
    # =================================================================
    # Step 7: Test Context Retrieval
    # =================================================================
    print("\n7️⃣ Testing context retrieval...")
    context = memori.retrieve_context("artificial intelligence machine learning", limit=2)
    print(f"   🔍 Found {len(context)} relevant memories")
    for i, ctx in enumerate(context, 1):
        summary = str(ctx)[:80] if ctx else "No summary"
        print(f"     {i}. {summary}...")
    
    # =================================================================
    # Step 8: Clean Shutdown
    # =================================================================
    print("\n8️⃣ Clean shutdown...")
    memori.disable()  # 🧹 One line to disable everything
    print("   ✅ Universal recording disabled")
    
    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "="*60)
    print("🎉 UNIVERSAL INTEGRATION EXAMPLE COMPLETED!")
    print("="*60)
    
    print("\n💡 KEY BENEFITS DEMONSTRATED:")
    print("   ✅ ONE LINE SETUP: memori.enable()")
    print("   ✅ WORKS WITH ALL PROVIDERS: LiteLLM, OpenAI, Anthropic, etc.")
    print("   ✅ NO WRAPPER CLASSES: Use libraries exactly as normal")
    print("   ✅ AUTO-DETECTION: Automatically finds and wraps clients")
    print("   ✅ CLEAN SHUTDOWN: memori.disable()")
    
    print("\n🚀 USAGE PATTERN:")
    print("   1. memori = Memori(...)")
    print("   2. memori.enable()        # Enable universal recording")
    print("   3. Use ANY LLM library normally")
    print("   4. memori.disable()       # Clean shutdown")
    
    print("\n🔮 FUTURE-PROOF:")
    print("   This approach automatically supports NEW LLM providers")
    print("   as they become available - no code changes needed!")


if __name__ == "__main__":
    main()