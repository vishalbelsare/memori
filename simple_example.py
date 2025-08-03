#!/usr/bin/env python3
"""
Simple example demonstrating Memori v1.0 Pydantic-based memory processing
"""

import os
from memoriai import Memori
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    print("🧠 Memori v1.0 - Pydantic-based Memory Example")
    print("=" * 50)

    # Initialize Memori with Pydantic-based processing
    office_work = Memori(
        database_connect="sqlite:///office_work_v1.db",
        template="basic",
        mem_prompt="Focus on programming concepts, code examples, and technical discussions",
        conscious_ingest=True,
        namespace="coding_workspace",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_id="developer_123",
    )

    # Update user context for better memory processing
    office_work.update_user_context(
        current_projects=["Flask API", "React Dashboard"],
        relevant_skills=["Python", "JavaScript", "REST APIs"],
        user_preferences=["Clean code", "Test-driven development"],
    )

    # Enable auto-recording (installs hooks into LLM libraries)
    office_work.enable()

    print("✅ Memori v1.0 enabled with Pydantic-based processing!")
    print(f"📊 Session ID: {office_work.session_id}")
    print(f"🏷️  Namespace: {office_work.namespace}")

    # Example: Manual conversation recording with structured processing
    print("\n📝 Recording conversation with structured processing...")
    chat_id = office_work.record_conversation(
        user_input="I'm learning about Python async/await for my Flask API project. How do I handle database connections asynchronously?",
        ai_output="For async database connections in Flask, you can use SQLAlchemy with asyncpg for PostgreSQL or aiomysql for MySQL. Create an async engine with create_async_engine(), use AsyncSession for database operations, and ensure your route handlers are async functions. Remember to await all database operations and properly handle connection pooling.",
        model="gpt-4o",
    )

    print(f"✅ Recorded conversation: {chat_id}")

    # Example: Auto-recording with LiteLLM (if installed)
    try:
        from litellm import completion

        print(
            "\n🤖 Making LiteLLM call (will be auto-recorded with structured processing)..."
        )
        response = completion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "What are Python type hints and why should I use them in my Flask project?",
                }
            ],
        )

        print("✅ LiteLLM response received and automatically processed!")
        print(f"📄 Response preview: {response.choices[0].message.content[:100]}...")

    except ImportError:
        print("❌ LiteLLM not installed, skipping auto-recording example")
    except Exception as e:
        print(f"❌ LiteLLM example failed: {e}")

    # Demonstrate advanced retrieval with entity search
    print("\n🔍 Testing advanced memory retrieval...")

    # Search by query
    context = office_work.retrieve_context("Python async database", limit=3)
    print(f"📊 Found {len(context)} memories for 'Python async database'")

    for i, item in enumerate(context, 1):
        summary = item.get("summary", "No summary available")
        category = item.get("category_primary", "unknown")
        importance = item.get("importance_score", 0)
        print(f"  {i}. [{category}] {summary[:80]}... (importance: {importance:.2f})")

    # Search by category
    print("\n📁 Searching for 'skill' category memories...")
    skill_memories = office_work.search_memories_by_category("skill", limit=3)
    print(f"📊 Found {len(skill_memories)} skill-related memories")

    for i, item in enumerate(skill_memories, 1):
        summary = item.get("summary", "No summary available")
        print(f"  {i}. {summary[:80]}...")

    # Search by entity
    print("\n🏷️  Searching for 'Flask' entity memories...")
    flask_memories = office_work.get_entity_memories("Flask", limit=2)
    print(f"📊 Found {len(flask_memories)} Flask-related memories")

    for i, item in enumerate(flask_memories, 1):
        summary = item.get("summary", "No summary available")
        print(f"  {i}. {summary[:80]}...")

    # Get comprehensive memory statistics
    stats = office_work.get_memory_stats()
    print("\n📈 Memory Statistics:")
    print(f"  💬 Chat History: {stats.get('chat_history_count', 0)}")
    print(f"  ⏱️  Short-term: {stats.get('short_term_count', 0)}")
    print(f"  🧠 Long-term: {stats.get('long_term_count', 0)}")
    print(f"  📋 Rules: {stats.get('rules_count', 0)}")
    print(f"  🏷️  Total Entities: {stats.get('total_entities', 0)}")
    print(f"  ⭐ Average Importance: {stats.get('average_importance', 0):.2f}")

    categories = stats.get("memories_by_category", {})
    if categories:
        print(f"  📊 By Category: {categories}")

    # Get integration statistics
    integration_stats = office_work.get_integration_stats()
    print(f"\n🔗 Integration Statistics: {len(integration_stats)} active integrations")
    for stat in integration_stats:
        print(
            f"  📡 {stat.get('integration')}: {stat.get('active_instances', 0)} instances"
        )

    # Example of manual memory recording with context
    print("\n💾 Recording additional context...")
    office_work.record_conversation(
        user_input="I prefer using SQLAlchemy ORM over raw SQL queries for better maintainability",
        ai_output="That's a great preference! SQLAlchemy ORM provides better code organization, type safety, and protection against SQL injection. It also makes database migrations easier to manage.",
        model="gpt-4o",
    )

    print("✅ Preference recorded and categorized!")

    # Show updated stats
    updated_stats = office_work.get_memory_stats()
    print("\n📈 Updated Statistics:")
    print(
        f"  📊 Total memories: {updated_stats.get('short_term_count', 0) + updated_stats.get('long_term_count', 0)}"
    )

    # Disable auto-recording
    office_work.disable()
    print("\n🔒 Memori disabled.")
    print("\n💡 Tip: Check 'office_work_v1.db' to see the structured memory storage!")
    print("🎉 Memori v1.0 demo completed!")


if __name__ == "__main__":
    main()
