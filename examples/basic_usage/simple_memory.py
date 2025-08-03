#!/usr/bin/env python3
"""
Simple Memory Example for Memoriai v1.0
Basic demonstration of memory storage and retrieval
"""

import os

from dotenv import load_dotenv

from memoriai import Memori

load_dotenv()


def main():
    print("🧠 Simple Memory Example - Memoriai v1.0")
    print("=" * 45)

    # Initialize basic memory system
    simple_memory = Memori(
        database_connect="sqlite:///simple_memory.db",
        template="basic",
        mem_prompt="Remember simple facts and preferences",
        conscious_ingest=True,
        namespace="simple_example",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    print("✅ Simple memory system initialized")

    # Enable memory processing
    simple_memory.enable()
    print("✅ Memory processing enabled!")

    # Record some simple conversations
    print("\n📝 Recording simple conversations...")

    conversations = [
        {
            "user": "My favorite color is blue",
            "ai": "I'll remember that your favorite color is blue. That's a nice preference to know!",
        },
        {
            "user": "Python is a programming language",
            "ai": "Yes, Python is a popular programming language known for its simplicity and versatility.",
        },
        {
            "user": "I work as a software developer",
            "ai": "That's great! As a software developer, you must work with various programming languages and technologies.",
        },
    ]

    chat_ids = []
    for i, conv in enumerate(conversations, 1):
        chat_id = simple_memory.record_conversation(
            user_input=conv["user"], ai_output=conv["ai"], model="simple-gpt-3.5-turbo"
        )
        chat_ids.append(chat_id)
        print(f"  {i}. Recorded: {chat_id[:8]}...")

    # Wait for processing
    import time

    time.sleep(2)

    # Retrieve memories
    print("\n🔍 Retrieving memories...")

    # Search for favorite color
    color_memories = simple_memory.retrieve_context("favorite color", limit=2)
    print(f"🎨 Color preferences: {len(color_memories)} found")
    for memory in color_memories:
        summary = memory.get("summary", "No summary")
        print(f"  - {summary}")

    # Search for Python
    python_memories = simple_memory.retrieve_context("Python programming", limit=2)
    print(f"🐍 Python-related: {len(python_memories)} found")
    for memory in python_memories:
        summary = memory.get("summary", "No summary")
        print(f"  - {summary}")

    # Get statistics
    stats = simple_memory.get_memory_stats()
    print("\n📊 Memory Stats:")
    print(f"  💬 Conversations: {stats.get('chat_history_count', 0)}")
    print(
        f"  🧠 Memories: {stats.get('short_term_count', 0) + stats.get('long_term_count', 0)}"
    )

    # Clean up
    simple_memory.disable()
    print("\n✅ Simple memory example completed!")


if __name__ == "__main__":
    main()
