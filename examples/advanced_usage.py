#!/usr/bin/env python3
"""
Advanced Usage Example for Memoriai v1.0
Demonstrates advanced features: multiple namespaces, entity search, category filtering,
custom memory processing, and integration with LLM function calling
"""

import os
import json
from memoriai import (
    Memori,
    create_memory_search_tool,
)
from dotenv import load_dotenv

load_dotenv()


def main():
    print("🚀 Memoriai v1.0 - Advanced Usage Example")
    print("=" * 50)

    # Initialize multiple Memoriai instances with different configurations
    work_memory = Memori(
        database_connect="sqlite:///work_memory.db",
        template="basic",
        mem_prompt="Focus on work-related conversations, technical solutions, and project context",
        conscious_ingest=True,
        namespace="work_projects",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_id="developer_001",
    )

    learning_memory = Memori(
        database_connect="sqlite:///learning_memory.db",
        template="basic",
        mem_prompt="Remember learning resources, educational content, and skill development",
        conscious_ingest=True,
        namespace="learning_journey",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_id="learner_001",
    )

    print("✅ Multiple Memoriai instances initialized")

    # Enable both instances
    work_memory.enable()
    learning_memory.enable()
    print("✅ Both memory systems enabled!")

    # Advanced Example 1: Work-focused conversations
    print("\n💼 Advanced Example 1: Work Project Memory...")

    # Record technical discussions
    work_conversations = [
        {
            "user": "We need to implement caching for our API to improve performance",
            "ai": "For API caching, consider Redis for in-memory caching or implement HTTP caching headers. For database queries, use query-level caching with cache keys based on parameters. Monitor cache hit rates and set appropriate TTL values.",
            "model": "gpt-4o",
        },
        {
            "user": "What's the best way to handle database migrations in production?",
            "ai": "Use migration tools like Alembic for SQLAlchemy. Always backup before migrations, test on staging first, use blue-green deployments for zero downtime, and have rollback strategies ready. Consider feature flags for gradual rollouts.",
            "model": "gpt-4o",
        },
        {
            "user": "I prefer using Docker containers for consistent development environments",
            "ai": "Docker is excellent for environment consistency! Use multi-stage builds for optimization, .dockerignore for faster builds, and docker-compose for local development. Consider using dev containers in VS Code for team consistency.",
            "model": "gpt-4o",
        },
    ]

    work_chat_ids = []
    for conv in work_conversations:
        chat_id = work_memory.record_conversation(
            user_input=conv["user"], ai_output=conv["ai"], model=conv["model"]
        )
        work_chat_ids.append(chat_id)
        print(f"   📝 Recorded work conversation: {chat_id[:8]}...")

    # Advanced Example 2: Learning-focused conversations
    print("\n📚 Advanced Example 2: Learning Memory...")

    learning_conversations = [
        {
            "user": "I want to learn about microservices architecture",
            "ai": "Microservices break applications into small, independent services. Key concepts: service discovery, API gateways, event-driven communication, and containerization. Start with domain-driven design to identify service boundaries.",
            "model": "gpt-4o",
        },
        {
            "user": "What are the pros and cons of microservices vs monolith?",
            "ai": "Microservices: Pros - scalability, technology diversity, fault isolation. Cons - complexity, network overhead, distributed system challenges. Monolith: Pros - simplicity, easier debugging, transactions. Cons - scaling limitations, technology lock-in.",
            "model": "gpt-4o",
        },
    ]

    learning_chat_ids = []
    for conv in learning_conversations:
        chat_id = learning_memory.record_conversation(
            user_input=conv["user"], ai_output=conv["ai"], model=conv["model"]
        )
        learning_chat_ids.append(chat_id)
        print(f"   📚 Recorded learning conversation: {chat_id[:8]}...")

    # Wait for processing
    import time

    time.sleep(3)

    # Advanced Example 3: Entity-based search
    print("\n🔍 Advanced Example 3: Entity-based Memory Search...")

    # Search for Docker-related memories in work context
    docker_memories = work_memory.get_entity_memories("Docker", limit=3)
    print(f"🐳 Found {len(docker_memories)} Docker-related work memories:")
    for i, memory in enumerate(docker_memories, 1):
        summary = memory.get("summary", "No summary")
        print(f"   {i}. {summary[:70]}...")

    # Search for microservices in learning context
    microservices_memories = learning_memory.retrieve_context("microservices", limit=2)
    print(f"\n🏗️  Found {len(microservices_memories)} microservices learning memories:")
    for i, memory in enumerate(microservices_memories, 1):
        summary = memory.get("summary", "No summary")
        category = memory.get("category_primary", "unknown")
        print(f"   {i}. [{category}] {summary[:70]}...")

    # Advanced Example 4: Category-based filtering
    print("\n📁 Advanced Example 4: Category-based Memory Filtering...")

    # Get preferences from work memory
    work_preferences = work_memory.search_memories_by_category("preference", limit=3)
    print(f"⚙️  Work Preferences ({len(work_preferences)} found):")
    for i, pref in enumerate(work_preferences, 1):
        summary = pref.get("summary", "No summary")
        print(f"   {i}. {summary[:60]}...")

    # Get facts from learning memory
    learning_facts = learning_memory.search_memories_by_category("fact", limit=3)
    print(f"\n📋 Learning Facts ({len(learning_facts)} found):")
    for i, fact in enumerate(learning_facts, 1):
        summary = fact.get("summary", "No summary")
        importance = fact.get("importance_score", 0)
        print(f"   {i}. {summary[:60]}... (importance: {importance:.2f})")

    # Advanced Example 5: Memory search tools for LLM integration
    print("\n🔧 Advanced Example 5: Memory Search Tools...")

    # Create search tools for both contexts
    work_search_tool = create_memory_search_tool(work_memory)
    learning_search_tool = create_memory_search_tool(learning_memory)

    # Simulate LLM function calling
    print("🤖 Simulating LLM function calls with memory search...")

    # Work context search
    work_search_result = work_search_tool("caching performance", max_results=2)
    work_data = json.loads(work_search_result)
    print(f"   💼 Work search found {work_data['found']} caching-related memories")

    # Learning context search
    learning_search_result = learning_search_tool(
        "architecture patterns", max_results=2
    )
    learning_data = json.loads(learning_search_result)
    print(
        f"   📚 Learning search found {learning_data['found']} architecture-related memories"
    )

    # Advanced Example 6: Memory analytics and insights
    print("\n📊 Advanced Example 6: Memory Analytics...")

    def print_detailed_stats(memory_instance, context_name):
        stats = memory_instance.get_memory_stats()
        print(f"\n{context_name} Memory Analytics:")
        print(f"  💬 Total Conversations: {stats.get('chat_history_count', 0)}")
        print(f"  ⏱️  Short-term: {stats.get('short_term_count', 0)}")
        print(f"  🧠 Long-term: {stats.get('long_term_count', 0)}")
        print(f"  📋 Rules: {stats.get('rules_count', 0)}")
        print(f"  🏷️  Entities: {stats.get('total_entities', 0)}")
        print(f"  ⭐ Avg Importance: {stats.get('average_importance', 0):.2f}")

        categories = stats.get("memories_by_category", {})
        if categories:
            print(f"  📊 Categories: {dict(categories)}")

    print_detailed_stats(work_memory, "🏢 Work")
    print_detailed_stats(learning_memory, "📚 Learning")

    # Advanced Example 7: Cross-context insights
    print("\n🔗 Advanced Example 7: Cross-Context Insights...")

    # Compare memory patterns between contexts
    work_stats = work_memory.get_memory_stats()
    learning_stats = learning_memory.get_memory_stats()

    print("Cross-Context Analysis:")
    print(f"  🏢 Work focus: {work_stats.get('chat_history_count', 0)} conversations")
    print(
        f"  📚 Learning focus: {learning_stats.get('chat_history_count', 0)} conversations"
    )

    work_entities = work_stats.get("total_entities", 0)
    learning_entities = learning_stats.get("total_entities", 0)
    total_entities = work_entities + learning_entities

    if total_entities > 0:
        work_ratio = (work_entities / total_entities) * 100
        learning_ratio = (learning_entities / total_entities) * 100
        print(
            f"  📊 Entity distribution: Work {work_ratio:.1f}% | Learning {learning_ratio:.1f}%"
        )

    # Advanced Example 8: Memory export and insights
    print("\n💾 Advanced Example 8: Memory Export...")

    # Get recent memories for export
    recent_work = work_memory.get_conversation_history(limit=2)
    recent_learning = learning_memory.get_conversation_history(limit=2)

    export_data = {
        "work_context": {
            "namespace": work_memory.namespace,
            "recent_conversations": len(recent_work),
            "stats": work_stats,
        },
        "learning_context": {
            "namespace": learning_memory.namespace,
            "recent_conversations": len(recent_learning),
            "stats": learning_stats,
        },
    }

    print("📄 Export data structure created")
    print(f"   🔢 Total data points: {len(export_data)} contexts")

    # Clean up
    work_memory.disable()
    learning_memory.disable()
    print("\n🔒 All memory systems disabled")

    print("\n💡 Advanced Usage Summary:")
    print("   ✅ Multiple namespace isolation")
    print("   ✅ Entity-based memory search")
    print("   ✅ Category-based filtering")
    print("   ✅ LLM integration tools")
    print("   ✅ Cross-context analytics")
    print("   ✅ Memory export capabilities")

    print("\n🎉 Advanced usage example completed!")
    print("💾 Check work_memory.db and learning_memory.db for stored data")


if __name__ == "__main__":
    main()
