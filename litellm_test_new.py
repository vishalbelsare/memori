#!/usr/bin/env python3
"""
Updated LiteLLM test using direct system prompt injection instead of interceptors.
This approach is more reliable than the interceptor-based method.
"""

from litellm import completion
from memori import Memori

# Test both modes
print("Choose mode:")
print("1. conscious_ingest (one-time complete memory injection)")
print("2. auto_ingest (dynamic relevant memory injection)")
mode = input("Enter 1 or 2: ").strip()

if mode == "1":
    print("🧠 Using conscious_ingest mode")
    litellm_memory = Memori(
        database_connect="sqlite:///patch-4.db",  # Use patch-4.db which has our test data
        conscious_ingest=True,
        verbose=True,
    )
elif mode == "2":
    print("🔍 Using auto_ingest mode")
    litellm_memory = Memori(
        database_connect="sqlite:///patch-4.db",  # Use patch-4.db which has our test data
        auto_ingest=True,
        verbose=True,
    )
else:
    print("❌ Invalid mode, using conscious_ingest as default")
    litellm_memory = Memori(
        database_connect="sqlite:///patch-4.db",
        conscious_ingest=True,
        verbose=True,
    )

# Enable memori (for background processing and initialization)
litellm_memory.enable()

print(f"\n✅ Memori enabled")
print(f"💾 Database: patch-4.db")
print(f"🔄 Mode: conscious_ingest={litellm_memory.conscious_ingest}, auto_ingest={litellm_memory.auto_ingest}")
print("\n--- Instructions ---")
print("💡 The system will add memory context directly to your messages")
print("💡 For conscious_ingest: Complete memory added once at first call")
print("💡 For auto_ingest: Relevant memory added to each call")
print("💡 Try asking: 'What is my name?' or 'Where do I work?'")
print("=" * 60)

while True:
    user_input = input("\nYou: ")
    
    if user_input.lower() in ['quit', 'exit', 'q']:
        break
    
    # Create initial messages
    messages = [
        {
            "role": "user",
            "content": user_input
        }
    ]
    
    # Add memory context based on ingest mode
    messages_with_memory = litellm_memory.add_memory_to_messages(messages, user_input)
    
    # Show what's being sent (for debugging)
    if len(messages_with_memory) > len(messages):
        print(f"\n📋 System context added (length: {len(messages_with_memory[0]['content'])} chars)")
        # Show first 200 chars of system message
        print(f"🔍 Preview: {messages_with_memory[0]['content'][:200]}...")
    
    # Make the LiteLLM call with memory context
    try:
        response = completion(
            model="gpt-4o",
            messages=messages_with_memory
        )
        
        ai_response = response.choices[0].message.content
        print(f"\nAI: {ai_response}")
        
        # Record the conversation in Memori
        litellm_memory.record(user_input, ai_response)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Note: Make sure you have proper API keys configured")

print("\n👋 Goodbye!")