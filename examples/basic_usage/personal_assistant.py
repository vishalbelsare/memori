#!/usr/bin/env python3
"""
Personal Assistant Example for Memoriai v1.0
Demonstrates building a personal assistant with memory capabilities
"""

import os
from memoriai import Memori, create_memory_search_tool
from dotenv import load_dotenv
import time

load_dotenv()


def main():
    print("🤖 Personal Assistant Example - Memoriai v1.0")
    print("=" * 50)

    # Initialize personal assistant memory
    assistant_memory = Memori(
        database_connect="sqlite:///personal_assistant.db",
        template="basic",
        mem_prompt="Act as a personal assistant. Remember user preferences, important dates, tasks, and personal information",
        conscious_ingest=True,
        namespace="personal_assistant",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_id="user_123",
    )

    print("✅ Personal assistant memory initialized")

    # Enable memory processing
    assistant_memory.enable()
    print("✅ Memory processing enabled!")
    print(f"🆔 User ID: {assistant_memory.user_id}")
    print(f"📊 Session: {assistant_memory.session_id}")

    # Simulate personal assistant conversations
    print("\n💬 Personal Assistant Conversations...")

    assistant_conversations = [
        {
            "user": "My birthday is on March 15th",
            "ai": "I've noted that your birthday is on March 15th. I'll remember this important date for you!",
        },
        {
            "user": "I have a meeting with John tomorrow at 2 PM",
            "ai": "I've recorded your meeting with John tomorrow at 2 PM. Would you like me to remind you before the meeting?",
        },
        {
            "user": "I prefer coffee over tea in the mornings",
            "ai": "Got it! I'll remember that you prefer coffee over tea in the mornings. This will help me make better suggestions.",
        },
        {
            "user": "Remind me to call my mom this weekend",
            "ai": "I'll remind you to call your mom this weekend. Family time is important!",
        },
        {
            "user": "I'm learning Spanish and practice 30 minutes daily",
            "ai": "That's wonderful! I've noted that you're learning Spanish with 30 minutes of daily practice. Consistency is key to language learning!",
        },
    ]

    print("Recording personal conversations...")
    for i, conv in enumerate(assistant_conversations, 1):
        chat_id = assistant_memory.record_conversation(
            user_input=conv["user"],
            ai_output=conv["ai"],
            model="personal-assistant-gpt-4o",
        )
        print(f"  {i}. Personal info recorded: {chat_id[:8]}...")

    # Wait for memory processing
    time.sleep(3)

    # Demonstrate assistant memory retrieval
    print("\n🔍 Assistant Memory Retrieval...")

    # Search for personal preferences
    preferences = assistant_memory.search_memories_by_category("preference", limit=3)
    print(f"⚙️  Personal Preferences ({len(preferences)} found):")
    for i, pref in enumerate(preferences, 1):
        summary = pref.get("summary", "No summary")
        print(f"  {i}. {summary}")

    # Search for important dates
    dates_context = assistant_memory.retrieve_context("birthday meeting", limit=3)
    print(f"\n📅 Important Dates & Events ({len(dates_context)} found):")
    for i, event in enumerate(dates_context, 1):
        summary = event.get("summary", "No summary")
        print(f"  {i}. {summary}")

    # Search for tasks and reminders
    tasks_context = assistant_memory.retrieve_context("remind call", limit=2)
    print(f"\n📋 Tasks & Reminders ({len(tasks_context)} found):")
    for i, task in enumerate(tasks_context, 1):
        summary = task.get("summary", "No summary")
        print(f"  {i}. {summary}")

    # Demonstrate context-aware assistant responses
    print("\n🤖 Context-Aware Assistant Responses...")

    # Create memory search tool for the assistant
    memory_tool = create_memory_search_tool(assistant_memory)

    # Simulate assistant queries
    assistant_queries = [
        "user preferences morning drinks",
        "user learning activities",
        "upcoming meetings",
    ]

    for query in assistant_queries:
        result = memory_tool(query, max_results=2)
        print(f"🔍 Query: '{query}'")

        import json

        try:
            data = json.loads(result)
            if data.get("found", 0) > 0:
                for memory in data["memories"]:
                    summary = memory.get("summary", "No summary")
                    print(f"  💡 Context: {summary[:60]}...")
            else:
                print("  📭 No relevant context found")
        except json.JSONDecodeError:
            print("  📄 Raw result available")
        print()

    # Simulate context-aware conversation
    print("🤖 Context-Aware Conversation Simulation...")

    # Get context for a morning routine question
    morning_context = assistant_memory.retrieve_context(
        "morning coffee preference", limit=1
    )
    context_summary = ""
    if morning_context:
        context_summary = morning_context[0].get("summary", "")

    # Simulate context-aware response
    context_aware_chat_id = assistant_memory.record_conversation(
        user_input="What should I have for breakfast this morning?",
        ai_output="Based on your preferences (you prefer coffee over tea in the mornings), I'd suggest having coffee with your breakfast. For food, consider something protein-rich like eggs or yogurt to start your day well!",
        model="context-aware-assistant",
        metadata={"context_used": context_summary[:50] if context_summary else "none"},
    )

    print(f"✅ Context-aware conversation: {context_aware_chat_id[:8]}...")
    print(
        f"📝 Used context: {context_summary[:50] if context_summary else 'No specific context'}..."
    )

    # Personal assistant statistics
    print("\n📊 Personal Assistant Statistics...")

    stats = assistant_memory.get_memory_stats()
    print("Assistant Memory Stats:")
    print(f"  💬 Total Conversations: {stats.get('chat_history_count', 0)}")
    print(
        f"  🧠 Total Memories: {stats.get('short_term_count', 0) + stats.get('long_term_count', 0)}"
    )
    print(f"  📋 Rules & Preferences: {stats.get('rules_count', 0)}")
    print(f"  🏷️  Total Entities: {stats.get('total_entities', 0)}")

    categories = stats.get("memories_by_category", {})
    if categories:
        print("  📊 Memory Categories:")
        for category, count in categories.items():
            print(f"     - {category}: {count}")

    # Export personal data
    print("\n💾 Personal Data Export...")
    recent_history = assistant_memory.get_conversation_history(limit=5)

    personal_export = {
        "user_id": assistant_memory.user_id,
        "namespace": assistant_memory.namespace,
        "total_conversations": len(recent_history),
        "memory_stats": stats,
        "export_timestamp": time.time(),
    }

    print("📄 Personal data export ready")
    print(f"🔢 Export contains {len(personal_export)} data sections")

    # Clean up
    assistant_memory.disable()
    print("\n🔒 Personal assistant memory disabled")

    print("\n💡 Personal Assistant Features Demonstrated:")
    print("   ✅ Personal preference tracking")
    print("   ✅ Important date remembering")
    print("   ✅ Task and reminder storage")
    print("   ✅ Context-aware responses")
    print("   ✅ Memory-based recommendations")
    print("   ✅ Personal data management")

    print("\n🎉 Personal assistant example completed!")
    print("💾 Check 'personal_assistant.db' for stored personal data")


if __name__ == "__main__":
    main()
