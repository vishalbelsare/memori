#!/usr/bin/env python3
"""
Basic Usage Example for Memoriai v1.0
Demonstrates core functionality with Pydantic-based memory processing
"""

import os
from memoriai import Memori, create_memory_search_tool
from dotenv import load_dotenv

load_dotenv()


def main():
    print("🧠 Memoriai v1.0 - Basic Usage Example")
    print("=" * 45)

    # Initialize Memoriai with basic configuration
    personal_memory = Memori(
        database_connect="sqlite:///personal_assistant.db",
        template="basic",
        mem_prompt="Remember personal preferences, learning topics, and important information",
        conscious_ingest=True,
        namespace="personal_assistant",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    print("✅ Memoriai initialized with basic configuration")

    # Enable Pydantic-based memory processing
    personal_memory.enable()
    print("✅ Memory processing enabled!")
    print(f"📊 Session ID: {personal_memory.session_id}")
    print(f"🏷️  Namespace: {personal_memory.namespace}")

    # Example 1: Record a learning conversation
    print("\n📝 Example 1: Recording a learning conversation...")
    chat_id_1 = personal_memory.record_conversation(
        user_input="I'm interested in learning machine learning. What should I start with?",
        ai_output="I'd recommend starting with Python basics, then moving to libraries like pandas for data manipulation, matplotlib for visualization, and scikit-learn for machine learning algorithms. Begin with supervised learning concepts like linear regression and classification.",
        model="gpt-4o",
    )
    print(f"✅ Learning conversation recorded: {chat_id_1}")

    # Example 2: Record a preference
    print("\n📝 Example 2: Recording a user preference...")
    chat_id_2 = personal_memory.record_conversation(
        user_input="I prefer learning through hands-on projects rather than just reading theory",
        ai_output="That's a great learning approach! Hands-on projects help reinforce concepts and build practical skills. I'll keep that in mind for future recommendations.",
        model="gpt-4o",
    )
    print(f"✅ Preference recorded: {chat_id_2}")

    # Example 3: Record technical information
    print("\n📝 Example 3: Recording technical information...")
    chat_id_3 = personal_memory.record_conversation(
        user_input="What's the difference between supervised and unsupervised learning?",
        ai_output="Supervised learning uses labeled training data to learn patterns (like classification and regression), while unsupervised learning finds hidden patterns in unlabeled data (like clustering and dimensionality reduction). Examples: supervised - email spam detection; unsupervised - customer segmentation.",
        model="gpt-4o",
    )
    print(f"✅ Technical information recorded: {chat_id_3}")

    # Wait a moment for processing (in real scenarios, this happens asynchronously)
    import time

    time.sleep(2)

    # Example 4: Search and retrieve memories
    print("\n🔍 Example 4: Searching stored memories...")

    # Search for machine learning related memories
    ml_context = personal_memory.retrieve_context("machine learning", limit=3)
    print(f"📊 Found {len(ml_context)} machine learning related memories:")

    for i, memory in enumerate(ml_context, 1):
        summary = memory.get("summary", "No summary available")
        category = memory.get("category_primary", "unknown")
        importance = memory.get("importance_score", 0)
        print(
            f"  {i}. [{category.upper()}] {summary[:60]}... (score: {importance:.2f})"
        )

    # Example 5: Use memory search tool
    print("\n🔧 Example 5: Using memory search tool...")
    search_tool = create_memory_search_tool(personal_memory)
    search_result = search_tool("learning preferences", max_results=2)
    print("📋 Search tool result:")
    print(f"   {search_result[:200]}...")

    # Example 6: View memory statistics
    print("\n📈 Example 6: Memory statistics...")
    stats = personal_memory.get_memory_stats()
    print("Memory Statistics:")
    print(f"  💬 Total Conversations: {stats.get('chat_history_count', 0)}")
    print(f"  ⏱️  Short-term Memories: {stats.get('short_term_count', 0)}")
    print(f"  🧠 Long-term Memories: {stats.get('long_term_count', 0)}")
    print(f"  📋 Rules & Preferences: {stats.get('rules_count', 0)}")
    print(f"  🏷️  Total Entities: {stats.get('total_entities', 0)}")

    categories = stats.get("memories_by_category", {})
    if categories:
        print("  📊 By Category:")
        for category, count in categories.items():
            print(f"     - {category}: {count}")

    # Clean up
    personal_memory.disable()
    print("\n🔒 Memory processing disabled")
    print("\n💡 Tips:")
    print("   - Check 'personal_assistant.db' to see stored memories")
    print("   - Memory processing happens automatically with conscious_ingest=True")
    print("   - Use different namespaces to separate memory contexts")
    print("\n🎉 Basic usage example completed!")


if __name__ == "__main__":
    main()
