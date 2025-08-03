#!/usr/bin/env python3
"""
LangChain Integration Example for Memoriai v1.0
Demonstrates automatic conversation recording with LangChain and Memoriai
"""

import os
from memoriai import Memori, create_memory_search_tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    print("🦜 Memoriai v1.0 + LangChain Integration Example")
    print("=" * 50)

    # Check if LangChain is available
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage

        print("✅ LangChain is available")
    except ImportError:
        print(
            "❌ LangChain not installed. Install with: pip install langchain langchain-openai"
        )
        print("   This example requires LangChain for integration testing")
        return

    # Initialize Memoriai for LangChain integration
    langchain_memory = Memori(
        database_connect="sqlite:///langchain_memory.db",
        template="basic",
        mem_prompt="Remember LangChain conversations, AI chains, and agent interactions",
        conscious_ingest=True,
        namespace="langchain_experiments",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    print("✅ Memoriai initialized for LangChain integration")

    # Enable auto-recording (may capture some LangChain calls)
    langchain_memory.enable()
    print("✅ Auto-recording enabled!")
    print(f"📊 Session ID: {langchain_memory.session_id}")

    # Example 1: Basic LangChain conversation
    print("\n🦜 Example 1: Basic LangChain conversation...")

    try:
        # Initialize LangChain ChatOpenAI
        chat = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        # Create messages
        messages = [
            SystemMessage(
                content="You are a helpful AI assistant specializing in LangChain and AI development."
            ),
            HumanMessage(
                content="What are the main components of LangChain and how do they work together?"
            ),
        ]

        # Get response (may be auto-recorded depending on LangChain integration)
        response = chat.invoke(messages)
        ai_response = response.content

        print("✅ LangChain conversation completed!")
        print(f"📄 Response preview: {ai_response[:100]}...")

        # Manual recording to ensure it's captured
        chat_id = langchain_memory.record_conversation(
            user_input="What are the main components of LangChain and how do they work together?",
            ai_output=ai_response,
            model="langchain-gpt-3.5-turbo",
        )
        print(f"✅ Manually recorded conversation: {chat_id[:8]}...")

    except Exception as e:
        print(f"❌ LangChain conversation failed: {e}")
        return

    # Example 2: Chain-based conversation
    print("\n⛓️  Example 2: LangChain Chain conversation...")

    try:
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain

        # Create a prompt template
        prompt = PromptTemplate(
            input_variables=["topic"],
            template="Explain {topic} in the context of building AI applications with LangChain. Focus on practical implementation.",
        )

        # Create an LLM chain
        chain = LLMChain(llm=chat, prompt=prompt)

        # Run the chain
        topics = ["vector databases", "prompt engineering", "agent architectures"]

        for topic in topics:
            try:
                result = chain.run(topic=topic)
                print(f"   🔗 Chain result for '{topic}': {result[:50]}...")

                # Record the chain interaction
                chain_chat_id = langchain_memory.record_conversation(
                    user_input=f"Explain {topic} in the context of building AI applications with LangChain",
                    ai_output=result,
                    model="langchain-chain-gpt-3.5-turbo",
                )
                print(f"   ✅ Recorded chain conversation: {chain_chat_id[:8]}...")

            except Exception as e:
                print(f"   ❌ Chain failed for {topic}: {e}")
                continue

    except ImportError:
        print("❌ LangChain chains not available, skipping chain example")
    except Exception as e:
        print(f"❌ Chain example failed: {e}")

    # Example 3: Memory-augmented responses
    print("\n🧠 Example 3: Memory-augmented LangChain responses...")

    # Create memory search tool
    memory_search_tool = create_memory_search_tool(langchain_memory)

    # Search for relevant memories
    search_result = memory_search_tool("LangChain components", max_results=2)
    print("📋 Memory search for LangChain components:")

    import json

    try:
        search_data = json.loads(search_result)
        if search_data.get("found", 0) > 0:
            print(f"   📊 Found {search_data['found']} relevant memories")
            for i, memory in enumerate(search_data["memories"], 1):
                summary = memory.get("summary", "No summary")
                print(f"   {i}. {summary[:70]}...")
        else:
            print("   📭 No relevant memories found yet")
    except json.JSONDecodeError:
        print(f"   📄 Raw result: {search_result[:100]}...")

    # Example 4: Agent-style interaction with memory context
    print("\n🤖 Example 4: Agent-style interaction with memory...")

    try:
        # Get memory context for the next conversation
        memory_context = langchain_memory.retrieve_context("vector databases", limit=2)

        context_text = ""
        if memory_context:
            context_text = "\n".join(
                [f"- {item.get('summary', 'No summary')}" for item in memory_context]
            )

        # Create context-aware prompt
        context_prompt = f"""
You are an AI assistant with access to previous conversation context.

Previous relevant context:
{context_text if context_text else "No previous context available"}

Based on this context and your knowledge, please respond to the user's question.
"""

        messages_with_context = [
            SystemMessage(content=context_prompt),
            HumanMessage(
                content="How should I choose between different vector database solutions for my LangChain application?"
            ),
        ]

        # Get context-aware response
        context_response = chat.invoke(messages_with_context)
        context_ai_response = context_response.content

        print("✅ Context-aware response generated!")
        print(f"📄 Context-aware response preview: {context_ai_response[:100]}...")

        # Record the context-aware conversation
        context_chat_id = langchain_memory.record_conversation(
            user_input="How should I choose between different vector database solutions for my LangChain application?",
            ai_output=context_ai_response,
            model="langchain-context-aware-gpt-3.5-turbo",
        )
        print(f"✅ Context-aware conversation recorded: {context_chat_id[:8]}...")

    except Exception as e:
        print(f"❌ Context-aware conversation failed: {e}")

    # Wait for memory processing
    import time

    time.sleep(2)

    # Example 5: LangChain integration statistics
    print("\n📈 Example 5: LangChain integration statistics...")

    stats = langchain_memory.get_memory_stats()
    integration_stats = langchain_memory.get_integration_stats()

    print("Memory Statistics:")
    print(f"  💬 Total Conversations: {stats.get('chat_history_count', 0)}")
    print(
        f"  🧠 Total Memories: {stats.get('short_term_count', 0) + stats.get('long_term_count', 0)}"
    )
    print(f"  🏷️  Total Entities: {stats.get('total_entities', 0)}")

    categories = stats.get("memories_by_category", {})
    if categories:
        print(f"  📊 Categories: {dict(categories)}")

    print("Integration Statistics:")
    print(f"  🔗 Active Integrations: {len(integration_stats)}")
    for stat in integration_stats:
        integration_name = stat.get("integration", "unknown")
        active_instances = stat.get("active_instances", 0)
        print(f"  📡 {integration_name}: {active_instances} instances")

    # Example 6: Export LangChain memories
    print("\n💾 Example 6: Export LangChain memories...")

    # Get conversation history
    recent_conversations = langchain_memory.get_conversation_history(limit=5)
    print(f"📚 Recent conversations: {len(recent_conversations)}")

    langchain_export = {
        "namespace": langchain_memory.namespace,
        "session_id": langchain_memory.session_id,
        "conversations": len(recent_conversations),
        "memory_stats": stats,
        "export_timestamp": time.time(),
    }

    print("📄 Export structure created for LangChain memories")

    # Example 7: Future integration possibilities
    print("\n🚀 Example 7: Future integration possibilities...")

    print("💡 Potential LangChain + Memoriai integrations:")
    print("   🔗 Custom memory retriever for LangChain chains")
    print("   🧠 Context-aware agent memory")
    print("   📊 Conversation analytics and insights")
    print("   🔍 Semantic search across chain interactions")
    print("   ⚡ Real-time memory updates during chain execution")

    # Clean up
    langchain_memory.disable()
    print("\n🔒 LangChain integration disabled")

    print("\n💡 Integration Summary:")
    print("   ✅ Manual conversation recording")
    print("   ✅ Chain interaction capture")
    print("   ✅ Memory-augmented responses")
    print("   ✅ Context-aware conversations")
    print("   ✅ Integration statistics")
    print("   ✅ Memory export capabilities")

    print("\n🎉 LangChain integration example completed!")
    print("💾 Check 'langchain_memory.db' for recorded interactions")


if __name__ == "__main__":
    main()
