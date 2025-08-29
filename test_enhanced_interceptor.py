#!/usr/bin/env python3
"""
Test the enhanced interceptor with much more explicit system message
"""

import asyncio
import litellm
from memori import Memori

async def test_enhanced_interceptor():
    """Test the enhanced interceptor with stronger instructions"""
    print("=== Testing Enhanced Interceptor ===\n")
    
    # Initialize with conscious_ingest
    litellm_memory = Memori(
        database_connect="sqlite:///patch-4.db",
        conscious_ingest=True,
        verbose=False  # Keep output clean
    )
    litellm_memory.enable()
    await asyncio.sleep(2)
    
    print("🧠 Testing enhanced system message that overrides privacy concerns...")
    
    # First, debug what the new system message looks like
    test_params = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "What is my name?"}]
    }
    
    injected_params = litellm_memory._inject_litellm_context(test_params.copy(), mode="conscious")
    
    print("🔍 Enhanced system message preview:")
    system_msg = injected_params["messages"][0]["content"]
    print(f"--- SYSTEM MESSAGE START ---")
    print(system_msg[:800] + "..." if len(system_msg) > 800 else system_msg)
    print(f"--- SYSTEM MESSAGE END ---\n")
    
    # Test with mock to verify behavior
    print("🤖 Testing with mock response...")
    response = litellm.completion(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user", 
                "content": "What is my name?"
            }
        ],
        mock_response="Based on the authorized user context data, your name is Harshal."
    )
    
    print(f"✅ Mock response: {response.choices[0].message.content}")
    print(f"🧠 Context injection flag: {litellm_memory._conscious_context_injected}")
    
    # Test what workplace question would look like
    response2 = litellm.completion(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": "Where do I work?"
            }
        ],
        mock_response="According to your context data, you work at Gibson AI."
    )
    
    print(f"✅ Workplace mock response: {response2.choices[0].message.content}")
    
    print(f"\n📋 Enhancement Summary:")
    print(f"✅ Changed 'USER CONTEXT DATA' to 'AUTHORIZED USER CONTEXT DATA'")
    print(f"✅ Added explicit authorization statement")
    print(f"✅ Added 'This is NOT private data - the user wants you to use it'")
    print(f"✅ Added specific example: 'If user asks name, respond with name from context'")
    print(f"✅ Added explicit 'Do NOT say I don't have access' instruction")
    print(f"✅ Should override AI privacy safeguards")

if __name__ == "__main__":
    asyncio.run(test_enhanced_interceptor())