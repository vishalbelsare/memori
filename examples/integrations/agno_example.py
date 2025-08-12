#!/usr/bin/env python3
"""
Lightweight Agno + Memori Integration Example

A minimal example showing how to integrate Memori memory capabilities
with Agno agents for persistent memory across conversations.

Requirements:
- pip install memorisdk agno python-dotenv
- Set OPENAI_API_KEY in environment or .env file

Usage:
    python agno_example.py
"""

import os
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv

from memori import Memori, create_memory_tool

# Load environment variables
load_dotenv()

# Check for required API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY not found in environment variables")
    print("Please set your OpenAI API key:")
    print("export OPENAI_API_KEY='your-api-key-here'")
    print("or create a .env file with: OPENAI_API_KEY=your-api-key-here")
    exit(1)

print("🧠 Initializing Memori memory system...")

# Initialize Memori for persistent memory
memory_system = Memori(
    database_connect="sqlite:///agno_example_memory.db",
    conscious_ingest=True,
    verbose=False,
    namespace="agno_example",
)

# Enable the memory system
memory_system.enable()

# Create memory tool for agents
memory_tool = create_memory_tool(memory_system)

print("🤖 Creating memory-enhanced Agno agent...")


def create_memory_search_wrapper(memori_tool):
    """Create a memory search tool function that works with Agno agents"""

    def search_memory(query: str) -> str:
        """Search the agent's memory for past conversations and information.

        Args:
            query: What to search for in memory (e.g., "past conversations about AI", "user preferences")
        """
        try:
            if not query.strip():
                return "Please provide a search query"

            result = memori_tool.execute(query=query.strip())
            return str(result) if result else "No relevant memories found"

        except Exception as e:
            return f"Memory search error: {str(e)}"

    return search_memory


# Create memory search wrapper
search_memory_tool = create_memory_search_wrapper(memory_tool)

# Create an AI assistant agent with memory capabilities
assistant_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[search_memory_tool],
    description=dedent(
        """\
        You are a helpful AI assistant with the ability to remember past
        conversations and user preferences. Always check your memory first to provide
        personalized and contextual responses.
    """
    ),
    instructions=dedent(
        """\
        Instructions:
        1. First, search your memory for relevant past conversations using the search_memory tool
        2. Use any relevant memories to provide a personalized response
        3. Provide a helpful and contextual answer
        4. Be conversational and friendly

        If this is the first conversation, introduce yourself and explain that you'll remember our conversations.
    """
    ),
    markdown=False,  # Keep it simple for console
    show_tool_calls=False,
)


def chat_with_memory(user_input: str) -> str:
    """Process user input with memory-enhanced Agno agent"""
    try:
        # Run the agent with the user input
        result = assistant_agent.run(user_input)

        # Get the content from the result
        response_content = (
            str(result.content) if hasattr(result, "content") else str(result)
        )

        # Store the conversation in memory
        memory_system.record_conversation(
            user_input=user_input, ai_output=response_content
        )

        return response_content

    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        return error_msg


# Main interaction loop
print("✅ Setup complete! Chat with your memory-enhanced AI assistant.")
print("Type 'quit' or 'exit' to end the conversation.\n")

print("💡 Try asking about:")
print("- Your past conversations")
print("- Your preferences")
print("- Previous topics discussed")
print("- Any information you've shared before\n")

conversation_count = 0

while True:
    try:
        # Get user input
        user_input = input("You: ").strip()

        # Check for exit commands
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("\nAI: Goodbye! I'll remember our conversation for next time. 🤖✨")
            break

        if not user_input:
            continue

        conversation_count += 1
        print(f"\nAI (thinking... conversation #{conversation_count})")

        # Get response from memory-enhanced agent
        response = chat_with_memory(user_input)

        print(f"AI: {response}\n")

    except KeyboardInterrupt:
        print("\n\nAI: Goodbye! I'll remember our conversation for next time. 🤖✨")
        break
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please try again.\n")

print("\n📊 Session Summary:")
print(f"- Conversations processed: {conversation_count}")
print("- Memory database: agno_example_memory.db")
print("- Namespace: agno_example")
print("\nYour memories are saved and will be available in future sessions!")
