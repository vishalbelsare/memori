#!/usr/bin/env python3
"""
Debug script to check Memori database contents and search functionality
"""

import os
import sqlite3
import sys

# Add current directory to path for memori import
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from memori import Memori  # noqa: E402


def check_database_contents(db_path="ollama_interactive.db"):
    """Check what's actually stored in the database"""
    print(f"🔍 Checking database: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return

    try:
        # Direct SQLite connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tables: {[t[0] for t in tables]}")

        # Check long-term memory
        cursor.execute("SELECT COUNT(*) FROM long_term_memory;")
        long_term_count = cursor.fetchone()[0]
        print(f"📚 Long-term memories: {long_term_count}")

        if long_term_count > 0:
            cursor.execute(
                "SELECT id, summary, content, classification, importance, created_at FROM long_term_memory ORDER BY created_at DESC LIMIT 5;"
            )
            memories = cursor.fetchall()
            print("\n🧠 Recent long-term memories:")
            for i, (
                _id,
                summary,
                content,
                classification,
                importance,
                created_at,
            ) in enumerate(memories, 1):
                print(f"  {i}. [{classification}] {summary}")
                print(f"     Content: {content[:100]}...")
                print(f"     Importance: {importance}")
                print(f"     Created: {created_at}\n")

        # Check chat history
        cursor.execute("SELECT COUNT(*) FROM conversation_history;")
        chat_count = cursor.fetchone()[0]
        print(f"💬 Chat history entries: {chat_count}")

        if chat_count > 0:
            cursor.execute(
                "SELECT user_message, ai_response, created_at FROM conversation_history ORDER BY created_at DESC LIMIT 3;"
            )
            chats = cursor.fetchall()
            print("\n💭 Recent chat history:")
            for i, (user_msg, ai_msg, created_at) in enumerate(chats, 1):
                print(f"  {i}. User: {user_msg}")
                print(f"     AI: {ai_msg[:80]}...")
                print(f"     Time: {created_at}\n")

        # Check FTS virtual table
        try:
            cursor.execute("SELECT COUNT(*) FROM long_term_memory_fts;")
            fts_count = cursor.fetchone()[0]
            print(f"🔍 FTS index entries: {fts_count}")
        except sqlite3.OperationalError as e:
            print(f"⚠️  FTS table issue: {e}")

        conn.close()

    except Exception as e:
        print(f"❌ Error reading database: {e}")


def test_memori_search():
    """Test Memori's search functionality"""
    print("\n🧪 Testing Memori search functionality...")

    try:
        # Initialize Memori with the same database
        memory = Memori(
            database_connect="sqlite:///ollama_interactive.db",
            conscious_ingest=False,  # Disable for testing
            auto_ingest=False,
            verbose=False,
        )

        # Get stats
        stats = memory.get_memory_stats()
        print(f"📊 Memori stats: {stats}")

        # Test different search approaches
        search_terms = ["harshal", "name", "work", "gibsonai", "memori"]

        for term in search_terms:
            print(f"\n🔍 Searching for '{term}':")

            # Try direct database search
            try:
                results = memory.db_manager.search_memories(term, limit=5)
                print(f"   Direct search: {len(results)} results")
                if results:
                    for r in results[:2]:
                        print(f"     - {r.get('summary', 'No summary')}")
            except Exception as e:
                print(f"   Direct search error: {e}")

            # Try search engine if available
            if memory.search_engine:
                try:
                    results = memory.search_engine.search_memories(term, limit=5)
                    print(f"   Search engine: {len(results)} results")
                except Exception as e:
                    print(f"   Search engine error: {e}")

    except Exception as e:
        print(f"❌ Error testing Memori search: {e}")


def main():
    """Main debug function"""
    print("🐛 Memori Debug Tool")
    print("=" * 50)

    # Check database contents
    check_database_contents()

    # Test search functionality
    test_memori_search()

    print("\n" + "=" * 50)
    print("✅ Debug complete!")


if __name__ == "__main__":
    main()
