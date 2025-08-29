#!/usr/bin/env python3
"""
Test with real OpenAI API to verify context injection
"""

import asyncio
import litellm
from memori import Memori

async def test_real_api():
    """Test with real API to verify context works"""
    print("=== Testing Real API Call ===\n")
    
    # Initialize Memori
    memori = Memori(
        database_connect="sqlite:///patch-4.db",
        namespace="default",
        conscious_ingest=True,
        auto_ingest=False
    )
    
    memori.enable()
    await asyncio.sleep(2)
    
    print(f"Context injection flag before call: {memori._conscious_context_injected}")
    
    # Test with mock first (should work)
    print("\n🔄 Mock call test:")
    mock_response = litellm.completion(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "What is my name and where do I work?"}
        ],
        mock_response="Based on your context, your name is Harshal and you work at Gibson AI."
    )
    
    print(f"Mock Response: {mock_response.choices[0].message.content}")
    print(f"Context flag after mock: {memori._conscious_context_injected}")
    
    # Now check what parameters were actually sent
    print("\n🔍 Checking parameters that would be sent:")
    test_params = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "What is my name and where do I work?"}
        ]
    }
    
    # Reset the flag to test injection again
    memori._conscious_context_injected = False
    injected = memori._inject_litellm_context(test_params.copy(), mode="conscious")
    
    print("Parameters that would be sent to API:")
    for msg in injected["messages"]:
        if msg["role"] == "system":
            print("✅ System message found:")
            print(msg["content"][:300] + "..." if len(msg["content"]) > 300 else msg["content"])
        else:
            print(f"User message: {msg['content']}")

if __name__ == "__main__":
    asyncio.run(test_real_api())