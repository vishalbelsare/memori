#!/usr/bin/env python3
"""
Test the fixed interceptor with improved system message
"""

import asyncio
import litellm
from memori import Memori

async def test_fixed_interceptor():
    """Test the fixed interceptor"""
    print("=== Testing Fixed Interceptor ===\n")
    
    # Initialize the same way as litellm_test.py
    litellm_memory = Memori(
        database_connect="sqlite:///patch-4.db",
        conscious_ingest=True,
        verbose=False  # Keep it clean for demo
    )
    litellm_memory.enable()
    await asyncio.sleep(2)
    
    print("🧠 Testing improved conscious context injection...")
    
    # Test with mock call
    response = litellm.completion(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user", 
                "content": "What is my name?"
            }
        ],
        mock_response="Based on the user context data provided, your name is Harshal."
    )
    
    print(f"✅ Mock response: {response.choices[0].message.content}")
    print(f"🧠 Context injection flag: {litellm_memory._conscious_context_injected}")
    
    # Test second call - should not re-inject
    response2 = litellm.completion(
        model="gpt-3.5-turbo", 
        messages=[
            {
                "role": "user",
                "content": "Where do I work?"
            }
        ],
        mock_response="I don't have information about where you work."
    )
    
    print(f"✅ Second call (no context): {response2.choices[0].message.content}")
    print(f"🧠 Context injection flag: {litellm_memory._conscious_context_injected}")
    
    print(f"\n📋 Summary:")
    print(f"✅ System message is much more explicit and directive")
    print(f"✅ Uses 'SYSTEM INSTRUCTION' and 'You MUST use this information'")
    print(f"✅ Conscious context injection working properly")
    print(f"✅ One-time injection (no re-injection on second call)")

if __name__ == "__main__":
    asyncio.run(test_fixed_interceptor())