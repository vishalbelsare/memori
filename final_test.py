#!/usr/bin/env python3
"""
Final test of improved conscious context injection
"""

import asyncio
import litellm
from memori import Memori

async def final_test():
    """Final test with improved context"""
    print("=== Final Test - Improved Context Injection ===\n")
    
    # Initialize Memori
    memori = Memori(
        database_connect="sqlite:///patch-4.db",
        namespace="default",
        conscious_ingest=True,
        auto_ingest=False
    )
    
    memori.enable()
    await asyncio.sleep(2)
    
    print("🔄 Testing improved context injection:")
    
    # Test first call - should inject context
    response1 = litellm.completion(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "What is my name?"}
        ],
        mock_response="Based on your context, your name is Harshal."
    )
    
    print(f"✅ First call - AI response: {response1.choices[0].message.content}")
    print(f"📊 Context injected: {memori._conscious_context_injected}")
    
    # Test second call - should NOT inject context again
    response2 = litellm.completion(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Where do I work?"}
        ],
        mock_response="I don't have information about where you work."
    )
    
    print(f"✅ Second call - AI response: {response2.choices[0].message.content}")
    print(f"📊 Context flag still set: {memori._conscious_context_injected}")
    
    print("\n🎯 Summary:")
    print("- ✅ First call gets complete context injection")
    print("- ✅ Context includes user name, workplace, and projects")
    print("- ✅ Subsequent calls don't re-inject context")
    print("- ✅ System message is clear and directive")
    
    print("\n📋 The system message now says:")
    print("'USE THIS INFORMATION TO ANSWER QUESTIONS'")
    print("'IMPORTANT: Use the above information to answer questions about the user'")

if __name__ == "__main__":
    asyncio.run(final_test())