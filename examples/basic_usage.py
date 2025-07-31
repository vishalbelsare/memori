"""
Basic usage example for Memori
"""

from memoriai import Memori
import time

def main():
    print("🧠 Memori Basic Usage Example")
    print("=" * 40)
    
    # Initialize Memori
    print("\n1. Initializing Memori...")
    memori = Memori(
        database_connect="sqlite:///example_memory.db",
        template="basic",
        mem_prompt="Remember important programming concepts and user preferences",
        conscious_ingest=True
    )
    
    # Enable memory recording
    print("2. Enabling memory recording...")
    memori.enable()
    print(f"   Session ID: {memori.session_id}")
    print(f"   Memory enabled: {memori.is_enabled}")
    
    # Simulate some conversations
    print("\n3. Recording conversations...")
    
    conversations = [
        {
            "user": "I prefer using Python for data analysis",
            "ai": "Great choice! Python has excellent libraries like pandas, numpy, and matplotlib for data analysis.",
            "model": "gpt-4"
        },
        {
            "user": "What is machine learning?",
            "ai": "Machine learning is a subset of AI that enables computers to learn and make decisions from data without being explicitly programmed for every task.",
            "model": "gpt-4"
        },
        {
            "user": "I always use pytest for testing my Python code",
            "ai": "Excellent! pytest is a powerful testing framework that makes it easy to write and run tests for Python applications.",
            "model": "gpt-4"
        }
    ]
    
    chat_ids = []
    for i, conv in enumerate(conversations, 1):
        print(f"   Recording conversation {i}...")
        chat_id = memori.record_conversation(
            user_input=conv["user"],
            ai_output=conv["ai"],
            model=conv["model"]
        )
        chat_ids.append(chat_id)
        time.sleep(0.1)  # Small delay for demonstration
    
    # Check memory statistics
    print("\n4. Memory Statistics:")
    stats = memori.get_memory_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Retrieve conversation history
    print("\n5. Recent Conversation History:")
    history = memori.get_conversation_history(limit=3)
    for i, conv in enumerate(history, 1):
        print(f"   Conversation {i}:")
        print(f"     User: {conv['user_input'][:50]}...")
        print(f"     AI: {conv['ai_output'][:50]}...")
        print(f"     Model: {conv['model']}")
        print()
    
    # Search for specific memories
    print("6. Searching memories for 'Python':")
    context = memori.retrieve_context("Python", limit=3)
    print(f"   Found {len(context)} relevant memories")
    
    # Demonstrate memory persistence
    print("\n7. Testing memory persistence...")
    memori.disable()
    
    # Create new instance (simulating restart)
    memori2 = Memori(database_connect="sqlite:///example_memory.db")
    memori2.enable()
    
    history2 = memori2.get_conversation_history(limit=3)
    print(f"   Retrieved {len(history2)} conversations after restart")
    print("   ✅ Memory persisted successfully!")
    
    print("\n" + "=" * 40)
    print("🎉 Example completed successfully!")
    print("\nMemory database saved as: example_memory.db")
    print("You can inspect it with any SQLite browser.")

if __name__ == "__main__":
    main()

