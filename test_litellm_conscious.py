#!/usr/bin/env python3
"""
Test conscious context injection with LiteLLM
"""

import asyncio
import litellm
from memori import Memori

async def test_litellm_conscious_context():
    """Test LiteLLM with conscious context injection"""
    print("=== Testing LiteLLM with Conscious Context ===\n")
    
    # Initialize Memori with conscious_ingest
    memori = Memori(
        database_connect="sqlite:///patch-4.db",
        namespace="default",
        conscious_ingest=True,
        auto_ingest=False
    )
    
    memori.enable()
    await asyncio.sleep(2)  # Wait for initialization
    
    print(f"✅ Memori enabled with conscious_ingest=True")
    print(f"📊 Context injection flag: {memori._conscious_context_injected}")
    
    # Test with a real LiteLLM call (mock mode)
    print("\n🔄 Testing LiteLLM call:")
    
    # First call - should inject context
    try:
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "What do you know about me? Please tell me my name and where I work."}
            ],
            mock_response="I can see from your context that your name is Harshal and you work at Gibson AI. You're working on product memory systems and use Python virtual environments for development."
        )
        
        print(f"✅ First call successful")
        print(f"📊 Context injection flag after first call: {memori._conscious_context_injected}")
        print(f"🤖 AI Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ First call failed: {e}")
    
    # Second call - should NOT inject context again
    print("\n🔄 Second LiteLLM call:")
    try:
        response2 = litellm.completion(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "user", "content": "What's my name again?"}
            ],
            mock_response="I don't have that information available to me right now."
        )
        
        print(f"✅ Second call successful")  
        print(f"📊 Context injection flag after second call: {memori._conscious_context_injected}")
        print(f"🤖 AI Response: {response2.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Second call failed: {e}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_litellm_conscious_context())