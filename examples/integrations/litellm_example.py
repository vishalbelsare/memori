#!/usr/bin/env python3
"""
LiteLLM Integration Example for Memoriai v1.0
Demonstrates automatic conversation recording with LiteLLM and Memoriai
"""

import os
from memoriai import Memori, create_memory_search_tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    print("🌟 Memoriai v1.0 + LiteLLM Integration Example")
    print("=" * 50)

    # Check if LiteLLM is available
    try:
        from litellm import completion

        print("✅ LiteLLM is available")
    except ImportError:
        print("❌ LiteLLM not installed. Install with: pip install litellm")
        print("   This example requires LiteLLM for automatic conversation recording")
        return

    # Initialize Memoriai for LiteLLM integration
    litellm_memory = Memori(
        database_connect="sqlite:///litellm_memory.db",
        template="basic",
        mem_prompt="Remember all LiteLLM conversations and AI interactions",
        conscious_ingest=True,
        namespace="litellm_conversations",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    print("✅ Memoriai initialized for LiteLLM integration")

    # Enable auto-recording (hooks into LiteLLM)
    litellm_memory.enable()
    print("✅ Auto-recording enabled for LiteLLM!")
    print(f"📊 Session ID: {litellm_memory.session_id}")

    # Example 1: Basic LiteLLM conversation (auto-recorded)
    print("\n🤖 Example 1: Basic LiteLLM conversation...")

    try:
        response1 = completion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "What are the benefits of using LiteLLM for multi-model AI applications?",
                }
            ],
        )

        ai_response = response1.choices[0].message.content
        print("✅ LiteLLM response received and auto-recorded!")
        print(f"📄 Response preview: {ai_response[:100]}...")

    except Exception as e:
        print(f"❌ LiteLLM call failed: {e}")
        return

    # Example 2: Multiple model conversations
    print("\n🔄 Example 2: Multiple model conversations...")

    models_to_test = ["gpt-3.5-turbo", "gpt-4o-mini"]

    for model in models_to_test:
        try:
            print(f"   🤖 Testing {model}...")
            response = completion(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": f"Explain the advantages of {model} in a concise way",
                    }
                ],
            )

            print(f"   ✅ {model} response auto-recorded!")

        except Exception as e:
            print(f"   ❌ {model} failed: {e}")
            continue

    # Example 3: Conversation with context (auto-recorded)
    print("\n💬 Example 3: Multi-turn conversation...")

    conversation_messages = [
        {
            "role": "user",
            "content": "I'm building a chatbot. What should I consider for memory management?",
        }
    ]

    try:
        # First turn
        response = completion(model="gpt-4o", messages=conversation_messages)

        ai_response = response.choices[0].message.content
        conversation_messages.append({"role": "assistant", "content": ai_response})
        print("✅ Turn 1 auto-recorded!")

        # Second turn
        conversation_messages.append(
            {"role": "user", "content": "How would Memoriai help with this use case?"}
        )

        response2 = completion(model="gpt-4o", messages=conversation_messages)

        print("✅ Turn 2 auto-recorded!")
        print(
            f"📄 Final response preview: {response2.choices[0].message.content[:100]}..."
        )

    except Exception as e:
        print(f"❌ Multi-turn conversation failed: {e}")

    # Wait for memory processing
    import time

    time.sleep(2)

    # Example 4: Search recorded LiteLLM conversations
    print("\n🔍 Example 4: Searching recorded conversations...")

    # Search for LiteLLM related memories
    litellm_context = litellm_memory.retrieve_context("LiteLLM benefits", limit=3)
    print(f"📊 Found {len(litellm_context)} LiteLLM-related memories:")

    for i, memory in enumerate(litellm_context, 1):
        summary = memory.get("summary", "No summary available")
        category = memory.get("category_primary", "unknown")
        model_used = memory.get("model", "unknown")
        print(f"  {i}. [{category}] {summary[:60]}... (model: {model_used})")

    # Example 5: Use memory search tool with LiteLLM context
    print("\n🔧 Example 5: Memory search tool...")

    search_tool = create_memory_search_tool(litellm_memory)
    search_result = search_tool("chatbot memory management", max_results=2)
    print("📋 Search results for 'chatbot memory management':")

    import json

    try:
        search_data = json.loads(search_result)
        if search_data.get("found", 0) > 0:
            for i, memory in enumerate(search_data["memories"], 1):
                summary = memory.get("summary", "No summary")
                category = memory.get("category", "unknown")
                print(f"  {i}. [{category}] {summary[:70]}...")
        else:
            print("  No relevant memories found")
    except json.JSONDecodeError:
        print(f"  Raw result: {search_result[:150]}...")

    # Example 6: Integration statistics
    print("\n📈 Example 6: LiteLLM integration statistics...")

    stats = litellm_memory.get_memory_stats()
    integration_stats = litellm_memory.get_integration_stats()

    print("Memory Statistics:")
    print(f"  💬 Total Conversations: {stats.get('chat_history_count', 0)}")
    print(
        f"  🧠 Total Memories: {stats.get('short_term_count', 0) + stats.get('long_term_count', 0)}"
    )
    print(f"  🏷️  Total Entities: {stats.get('total_entities', 0)}")

    print("Integration Statistics:")
    print(f"  🔗 Active Integrations: {len(integration_stats)}")
    for stat in integration_stats:
        integration_name = stat.get("integration", "unknown")
        active_instances = stat.get("active_instances", 0)
        print(f"  📡 {integration_name}: {active_instances} instances")

    # Example 7: Manual conversation recording alongside auto-recording
    print("\n📝 Example 7: Manual + automatic recording...")

    # Manual recording
    manual_chat_id = litellm_memory.record_conversation(
        user_input="I want to compare GPT-4 and Claude-3 for my use case",
        ai_output="Both models have strengths: GPT-4 excels at reasoning and code, while Claude-3 is strong at analysis and safety. Consider your specific needs: technical tasks favor GPT-4, while analytical writing might favor Claude-3.",
        model="manual-entry",
    )
    print(f"✅ Manual conversation recorded: {manual_chat_id[:8]}...")

    # Automatic recording via LiteLLM
    try:
        auto_response = completion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "What factors should I consider when choosing between different AI models?",
                }
            ],
        )
        print("✅ Automatic LiteLLM conversation recorded!")
    except Exception as e:
        print(f"❌ Automatic recording failed: {e}")

    # Final statistics
    final_stats = litellm_memory.get_memory_stats()
    print("\n📊 Final Statistics:")
    print(
        f"  📈 Total conversations processed: {final_stats.get('chat_history_count', 0)}"
    )

    # Clean up
    litellm_memory.disable()
    print("\n🔒 LiteLLM integration disabled")

    print("\n💡 Integration Benefits:")
    print("   ✅ Automatic conversation recording")
    print("   ✅ Multi-model support")
    print("   ✅ Seamless memory integration")
    print("   ✅ Structured conversation storage")
    print("   ✅ Searchable conversation history")

    print("\n🎉 LiteLLM integration example completed!")
    print("💾 Check 'litellm_memory.db' for recorded conversations")


if __name__ == "__main__":
    main()
