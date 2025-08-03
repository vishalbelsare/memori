"""
Example demonstrating the LiteLLM Native Callback System

This shows how to use Memori with LiteLLM's official callback system.
This is the most robust and "correct" way to integrate with LiteLLM.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
from memoriai import Memori
from dotenv import load_dotenv  

load_dotenv()
# Set up your API key (replace with your actual key)
# You can also use environment variable: export OPENAI_API_KEY="your-key"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def main():
    print("🧠 LiteLLM Native Callback System Example")
    print("=" * 50)
    
    # Initialize Memori
    print("\n1. Initializing Memori...")
    memori = Memori(
        database_connect="sqlite:///litellm_native_example.db",
        template="basic",
        conscious_ingest=True,
        namespace="litellm_demo"
    )
    print(f"✅ Memori initialized with namespace: {memori.namespace}")
    
    # Enable the native callback system
    print("\n2. Enabling native callback system...")
    memori.enable()  # This registers with LiteLLM's callback system
    print("✅ Native callback system enabled")
    
    # Now ANY LiteLLM call will automatically trigger memory recording
    try:
        from litellm import completion
        
        print("\n3. Making LiteLLM calls (these will be automatically recorded)...")
        
        # Call 1: Basic question
        print("\n🤖 Call 1: Basic question about Python")
        response1 = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "What are the key features of Python programming language?"}
            ]
        )
        print(f"Response: {response1.choices[0].message.content[:100]}...")
        
        # Call 2: Follow-up question that can use context
        print("\n🤖 Call 2: Follow-up question")
        response2 = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Can you give me a simple example of using those features?"}
            ]
        )
        print(f"Response: {response2.choices[0].message.content[:100]}...")
        
        # Call 3: Different topic
        print("\n🤖 Call 3: Different topic")
        response3 = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "What is machine learning?"}
            ]
        )
        print(f"Response: {response3.choices[0].message.content[:100]}...")
        
    except ImportError:
        print("❌ LiteLLM not installed. Install it with: pip install litellm")
        return
    except Exception as e:
        print(f"❌ Error making LiteLLM calls: {e}")
        return
    
    # Check memory statistics
    print("\n4. Checking memory statistics...")
    stats = memori.get_memory_stats()
    print(f"✅ Memory stats: {stats}")
    
    integration_stats = memori.get_integration_stats()
    print(f"✅ Integration stats: {integration_stats}")
    
    # Retrieve conversation history
    print("\n5. Retrieving conversation history...")
    history = memori.get_conversation_history(limit=5)
    print(f"✅ Found {len(history)} conversations in history")
    
    for i, conv in enumerate(history, 1):
        print(f"  Conversation {i}:")
        print(f"    User: {conv.get('user_input', '')[:50]}...")
        print(f"    AI: {conv.get('ai_output', '')[:50]}...")
        print(f"    Model: {conv.get('model', 'unknown')}")
    
    # Test context retrieval
    print("\n6. Testing context retrieval...")
    context = memori.retrieve_context("Python features", limit=3)
    print(f"✅ Found {len(context)} relevant memories for 'Python features'")
    
    for i, ctx in enumerate(context, 1):
        print(f"  Context {i}: {str(ctx)[:80]}...")
    
    # Disable the system
    print("\n7. Disabling Memori...")
    memori.disable()
    print("✅ Memori disabled - callbacks unregistered")
    
    print("\n🎉 Example completed successfully!")
    print("\nKey advantages of the native callback system:")
    print("• ✅ Uses LiteLLM's official extension mechanism")
    print("• ✅ No monkey-patching or global state modification")
    print("• ✅ Robust against LiteLLM updates")
    print("• ✅ Clean and safe implementation")
    print("• ✅ Perfect plug-and-play experience")

if __name__ == "__main__":
    main()