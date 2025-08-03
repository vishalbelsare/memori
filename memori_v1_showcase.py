"""
Memori v1.0 Comprehensive Showcase
Demonstrates the complete Pydantic-based memory processing system
"""

import os

from dotenv import load_dotenv

from memoriai.core.memory import Memori

# Load environment variables
load_dotenv()


def showcase_memori_v1():
    """Comprehensive demonstration of Memori v1.0 features"""

    print("🚀 Memori v1.0 - Comprehensive Feature Showcase")
    print("=" * 60)

    # Initialize Memori with comprehensive configuration
    personal_assistant = Memori(
        database_connect="sqlite:///memori_v1_showcase.db",
        template="basic",
        mem_prompt="Focus on learning, productivity, and personal development",
        conscious_ingest=True,
        namespace="personal_dev",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_id="learner_001",
    )

    # Configure user context for personalized processing
    personal_assistant.update_user_context(
        current_projects=[
            "Machine Learning Course",
            "Personal Finance App",
            "Python Automation Scripts",
        ],
        relevant_skills=[
            "Python",
            "Machine Learning",
            "Data Analysis",
            "Web Development",
            "Financial Planning",
        ],
        user_preferences=[
            "Practical examples over theory",
            "Step-by-step tutorials",
            "Open source tools",
            "Incremental learning approach",
        ],
    )

    personal_assistant.enable()

    print("✅ Memori v1.0 initialized with:")
    print(f"   📊 Session: {personal_assistant.session_id}")
    print(f"   🏷️  Namespace: {personal_assistant.namespace}")
    print(f"   🧠 Conscious Ingestion: {personal_assistant.conscious_ingest}")

    # === DEMONSTRATION 1: Learning Conversation ===
    print("\n" + "=" * 60)
    print("📚 DEMO 1: Learning Conversation Processing")
    print("=" * 60)

    learning_chat = personal_assistant.record_conversation(
        user_input="I'm struggling to understand gradient descent in machine learning. Can you explain it with a simple example?",
        ai_output="Gradient descent is like finding the bottom of a valley while blindfolded. Imagine you're standing on a hill and want to reach the lowest point. You feel the slope with your feet and take steps in the steepest downward direction. In ML, the 'hill' is your loss function, and you're trying to minimize prediction errors. You calculate gradients (slopes) of your parameters and adjust them step by step. For example, if you're predicting house prices, gradient descent helps you find the best weights for features like size, location, etc. The learning rate controls how big steps you take - too big and you might overshoot, too small and you'll take forever to converge.",
        model="gpt-4o",
    )

    print(f"📝 Recorded learning conversation: {learning_chat}")

    # === DEMONSTRATION 2: Preference Recording ===
    print("\n" + "=" * 60)
    print("⚙️ DEMO 2: Preference and Rule Recording")
    print("=" * 60)

    preference_chat = personal_assistant.record_conversation(
        user_input="I prefer using Jupyter notebooks for data exploration because I can see results immediately",
        ai_output="That's an excellent preference! Jupyter notebooks are perfect for interactive data exploration. The immediate visual feedback helps you understand your data better and iterate quickly. You can also document your thought process alongside the code, which is great for learning and sharing insights.",
        model="gpt-4o",
    )

    rule_chat = personal_assistant.record_conversation(
        user_input="Always backup my work before trying experimental code changes",
        ai_output="That's a crucial rule for any developer! Version control with Git is essential, and you should also consider using branches for experimental features. Tools like automated backups or cloud sync can provide additional safety nets.",
        model="gpt-4o",
    )

    print(f"🎯 Recorded preference: {preference_chat}")
    print(f"📋 Recorded rule: {rule_chat}")

    # === DEMONSTRATION 3: Context and Skills ===
    print("\n" + "=" * 60)
    print("🎯 DEMO 3: Context and Skill Development")
    print("=" * 60)

    skill_chat = personal_assistant.record_conversation(
        user_input="I just learned how to use pandas groupby() for data aggregation in my finance app project",
        ai_output="Great progress! pandas groupby() is incredibly powerful for financial data analysis. You can group by date, category, or account type and then aggregate with sum(), mean(), or custom functions. This will be perfect for your personal finance app - you could group expenses by month or category to create spending summaries and budgets.",
        model="gpt-4o",
    )

    context_chat = personal_assistant.record_conversation(
        user_input="For my finance app, I'm using Flask for the backend API and React for the frontend",
        ai_output="That's a solid tech stack! Flask is lightweight and perfect for APIs, while React gives you a dynamic frontend. Consider using Flask-CORS for handling cross-origin requests, and maybe SQLAlchemy for database operations. For authentication, Flask-JWT-Extended works well with React apps.",
        model="gpt-4o",
    )

    print(f"🧠 Recorded skill development: {skill_chat}")
    print(f"🏗️ Recorded project context: {context_chat}")

    # === DEMONSTRATION 4: Advanced Search and Retrieval ===
    print("\n" + "=" * 60)
    print("🔍 DEMO 4: Advanced Search and Retrieval")
    print("=" * 60)

    # Query-based search with intelligent planning
    print("🔍 Searching for 'machine learning' concepts...")
    ml_memories = personal_assistant.retrieve_context(
        "machine learning gradient descent", limit=3
    )
    print(f"📊 Found {len(ml_memories)} machine learning memories:")
    for i, memory in enumerate(ml_memories, 1):
        print(
            f"   {i}. [{memory.get('category_primary', 'unknown')}] {memory.get('summary', 'No summary')[:80]}..."
        )
        print(f"      💯 Importance: {memory.get('importance_score', 0):.2f}")

    # Category-based search
    print("\n📁 Searching preferences...")
    preferences = personal_assistant.search_memories_by_category("preference", limit=3)
    print(f"📊 Found {len(preferences)} preference memories:")
    for i, pref in enumerate(preferences, 1):
        print(f"   {i}. {pref.get('summary', 'No summary')[:80]}...")

    # Entity-based search
    print("\n🏷️ Searching for 'Flask' related memories...")
    flask_memories = personal_assistant.get_entity_memories("Flask", limit=2)
    print(f"📊 Found {len(flask_memories)} Flask-related memories:")
    for i, memory in enumerate(flask_memories, 1):
        print(f"   {i}. {memory.get('summary', 'No summary')[:80]}...")

    # === DEMONSTRATION 5: Memory Statistics and Analytics ===
    print("\n" + "=" * 60)
    print("📊 DEMO 5: Memory Analytics and Statistics")
    print("=" * 60)

    stats = personal_assistant.get_memory_stats()
    print("📈 Current Memory Statistics:")
    print(f"   💬 Chat History: {stats.get('chat_history_count', 0)}")
    print(f"   ⏱️ Short-term Memories: {stats.get('short_term_count', 0)}")
    print(f"   🧠 Long-term Memories: {stats.get('long_term_count', 0)}")
    print(f"   📋 Rules: {stats.get('rules_count', 0)}")
    print(f"   🏷️ Total Entities: {stats.get('total_entities', 0)}")
    print(f"   ⭐ Average Importance: {stats.get('average_importance', 0):.2f}")

    categories = stats.get("memories_by_category", {})
    if categories:
        print("   📊 By Category:")
        for category, count in categories.items():
            print(f"      • {category}: {count}")

    # === DEMONSTRATION 6: Integration Statistics ===
    print("\n" + "=" * 60)
    print("🔗 DEMO 6: Integration Status")
    print("=" * 60)

    integration_stats = personal_assistant.get_integration_stats()
    print(f"📡 Active Integrations: {len(integration_stats)}")
    for stat in integration_stats:
        print(
            f"   🔌 {stat.get('integration', 'unknown')}: {stat.get('active_instances', 0)} instances"
        )

    # === DEMONSTRATION 7: Auto-recording with LiteLLM ===
    print("\n" + "=" * 60)
    print("🤖 DEMO 7: Auto-recording Integration")
    print("=" * 60)

    try:
        from litellm import completion

        print("🚀 Making auto-recorded LiteLLM call...")
        response = completion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "What's the difference between supervised and unsupervised learning in my ML course context?",
                }
            ],
        )

        print("✅ Auto-recorded response:")
        print(f"   📄 Preview: {response.choices[0].message.content[:120]}...")

        # Check updated stats
        new_stats = personal_assistant.get_memory_stats()
        print(
            f"   📊 Updated total conversations: {new_stats.get('chat_history_count', 0)}"
        )

    except ImportError:
        print("❌ LiteLLM not installed - install with: pip install litellm")
    except Exception as e:
        print(f"❌ Auto-recording demo failed: {e}")

    # === DEMONSTRATION 8: Memory Export/Inspection ===
    print("\n" + "=" * 60)
    print("🔍 DEMO 8: Memory Inspection and Export")
    print("=" * 60)

    # Get recent conversation history
    recent_chats = personal_assistant.get_conversation_history(limit=3)
    print(f"📜 Recent Conversations ({len(recent_chats)}):")
    for i, chat in enumerate(recent_chats, 1):
        timestamp = chat.get("timestamp", "Unknown time")
        model = chat.get("model", "unknown")
        user_preview = chat.get("user_input", "")[:50]
        print(f"   {i}. [{model}] {timestamp}: {user_preview}...")

    # Final statistics
    final_stats = personal_assistant.get_memory_stats()
    total_memories = (
        final_stats.get("short_term_count", 0)
        + final_stats.get("long_term_count", 0)
        + final_stats.get("rules_count", 0)
    )

    print("\n🎯 Session Summary:")
    print(f"   💾 Total Memories Processed: {total_memories}")
    print(f"   🧠 Total Entities Extracted: {final_stats.get('total_entities', 0)}")
    print(
        f"   📊 Average Memory Importance: {final_stats.get('average_importance', 0):.2f}"
    )

    personal_assistant.disable()
    print("\n🔒 Memori disabled. Database saved to: memori_v1_showcase.db")

    # === SUMMARY ===
    print("\n" + "=" * 60)
    print("🎉 MEMORI v1.0 SHOWCASE COMPLETE!")
    print("=" * 60)
    print("✅ Demonstrated Features:")
    print("   🔧 Pydantic-based structured memory processing")
    print("   🧠 Intelligent entity extraction and categorization")
    print("   🔍 Advanced multi-strategy search capabilities")
    print("   📊 Comprehensive analytics and statistics")
    print("   🏷️ Entity-based and category-based filtering")
    print("   ⚡ Auto-recording with popular LLM libraries")
    print("   🎯 User context and preference management")
    print("   📈 Multi-dimensional importance scoring")
    print("   💾 Full-text search with SQLite FTS5")
    print("   🏗️ Robust error handling and fallbacks")

    print("\n💡 Next Steps:")
    print("   • Explore the database: sqlite3 memori_v1_showcase.db")
    print("   • Check memory_search_fts table for full-text search")
    print("   • Examine memory_entities table for entity indexing")
    print("   • Review processed_data JSON for structured memories")

    print("\n🚀 Memori v1.0 - The future of AI memory is here!")


if __name__ == "__main__":
    showcase_memori_v1()
