"""
Conscious Ingestion Example - Demonstrating automatic memory injection into LLM calls

This example shows how the conscious ingestion feature automatically retrieves
relevant memories and injects them into LLM API calls before execution.
"""

import os
from dotenv import load_dotenv
from memoriai.core.memory import Memori

# Load environment variables
load_dotenv()


def demonstrate_conscious_ingestion():
    """Demonstrate conscious ingestion with OpenAI integration"""
    
    print("🧠 Conscious Ingestion Demo - Automatic Memory Injection")
    print("=" * 60)
    
    # Initialize Memori with conscious ingestion enabled (default)
    memori = Memori(
        database_connect="sqlite:///conscious_ingestion_demo.db",
        template="basic",
        conscious_ingest=True,  # This enables automatic context injection
        namespace="conscious_demo",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_id="demo_user"
    )
    
    # Enable the memory system
    memori.enable()
    
    print(f"✅ Memori initialized:")
    print(f"   🏷️  Namespace: {memori.namespace}")
    print(f"   🧠 Conscious Ingestion: {memori.conscious_ingest}")
    
    # Record some initial conversations to build memory
    print("\n📝 Building initial memories...")
    
    memori.record_conversation(
        user_input="My name is Alice and I'm a software engineer",
        ai_output="Hello Alice! It's nice to meet you. Software engineering is a fantastic field.",
        model="gpt-4",
        metadata={"context": "introduction"}
    )
    
    memori.record_conversation(
        user_input="I'm working on a Python project using FastAPI",
        ai_output="FastAPI is an excellent choice for building APIs in Python. It's fast, modern, and has great documentation.",
        model="gpt-4",
        metadata={"context": "project_discussion"}
    )
    
    memori.record_conversation(
        user_input="I prefer using PostgreSQL for databases",
        ai_output="PostgreSQL is a robust choice for relational databases. It has excellent performance and features.",
        model="gpt-4",
        metadata={"context": "technology_preference"}
    )
    
    print("✅ Initial memories recorded")
    
    # Demonstrate context retrieval
    print("\n🔍 Testing context retrieval...")
    context = memori.retrieve_context("What database should I use for my API project?", limit=3)
    
    print(f"Retrieved {len(context)} relevant memories:")
    for i, mem in enumerate(context, 1):
        summary = mem.get('summary', '') or mem.get('content', '') or str(mem)
        print(f"  {i}. {summary[:100]}...")
    
    print("\n🚀 Conscious Ingestion in Action:")
    print("When you now make an LLM API call, relevant memories will be")
    print("automatically injected into the context. For example:")
    print()
    print("User query: 'What database should I use for my FastAPI project?'")
    print()
    print("The integration will automatically prepend relevant memories:")
    print("--- Relevant Memories ---")
    for mem in context[:2]:  # Show first 2 memories
        summary = mem.get('summary', '') or mem.get('content', '') or str(mem)
        print(f"- {summary[:80]}...")
    print("-------------------------")
    print("User query: What database should I use for my FastAPI project?")
    print()
    print("This context helps the LLM provide more personalized responses!")
    
    # Example with OpenAI (if available)
    try:
        import openai
        print("\n🔥 Live Demo with OpenAI:")
        print("Making an actual API call with conscious ingestion...")
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # This call will automatically include relevant memories
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "What database should I use for my API project?"}
            ],
            max_tokens=100
        )
        
        print("📤 Response (with conscious context):")
        print(response.choices[0].message.content)
        
    except ImportError:
        print("\n💡 Install OpenAI to see live conscious ingestion demo:")
        print("   pip install openai")
    except Exception as e:
        print(f"\n⚠️  OpenAI demo failed: {e}")
    
    # Clean up
    memori.disable()
    print("\n🧹 Demo completed and cleaned up")


if __name__ == "__main__":
    demonstrate_conscious_ingestion()