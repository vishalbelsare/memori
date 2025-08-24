#!/usr/bin/env python3
"""
OpenAI Agent + Memori Integration Example

A simple example showing how to integrate Memori memory capabilities
with OpenAI Agent for persistent memory across conversations.

Requirements:
- pip install memorisdk openai-agents
- Set OPENAI_API_KEY in environment: export OPENAI_API_KEY=sk-...

Usage:
    python openai_agent_example.py
"""

import asyncio
import os
from textwrap import dedent

from agents import Agent, Runner, function_tool
from pydantic import BaseModel

from memori import Memori, create_memory_tool

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
    database_connect="sqlite:///openai_agent_memory.db",
    conscious_ingest=True,
    verbose=False,
    namespace="openai_agent_example",
)

# Enable the memory system
memory_system.enable()

# Create memory tool for agents
memory_tool = create_memory_tool(memory_system)

print("🤖 Creating memory-enhanced OpenAI Agent...")


class MemorySearchResult(BaseModel):
    """Result model for memory search operations"""

    query: str
    results: str
    found_memories: bool


@function_tool
def search_memory(query: str) -> MemorySearchResult:
    """Search the agent's memory for past conversations, user preferences, and information.

    Args:
        query: What to search for in memory (e.g., "user preferences", "past conversations about AI", "my favorite topics")

    Returns:
        MemorySearchResult: Search results from the agent's memory
    """
    try:
        if not query.strip():
            return MemorySearchResult(
                query=query,
                results="Please provide a search query",
                found_memories=False,
            )

        print(f"[debug] Searching memory for: {query}")

        # Use the memory tool to search
        result = memory_tool.execute(query=query.strip())

        found_memories = bool(
            result
            and "No relevant memories found" not in result
            and "Error" not in result
        )

        return MemorySearchResult(
            query=query,
            results=result if result else "No relevant memories found",
            found_memories=found_memories,
        )

    except Exception as e:
        return MemorySearchResult(
            query=query, results=f"Memory search error: {str(e)}", found_memories=False
        )


class UserPreference(BaseModel):
    """Model for user preferences and information"""

    category: str
    preference: str
    context: str


@function_tool
def remember_user_info(category: str, preference: str, context: str) -> UserPreference:
    """Remember important information about the user for future conversations.

    Args:
        category: Type of information (e.g., "preference", "skill", "interest", "goal")
        preference: The specific preference or information to remember
        context: Additional context about this information

    Returns:
        UserPreference: Confirmation of what was remembered
    """
    try:
        print(f"[debug] Remembering user info: {category} - {preference}")

        # Store in memory system (this will be picked up automatically by Memori)
        memory_system.record_conversation(
            user_input=f"User shared {category}: {preference}",
            ai_output=f"I'll remember that you {preference}. {context}",
            metadata={
                "type": "user_preference",
                "category": category,
                "preference": preference,
                "context": context,
            },
        )

        return UserPreference(category=category, preference=preference, context=context)

    except Exception as e:
        return UserPreference(
            category=category,
            preference=f"Error storing preference: {str(e)}",
            context=context,
        )


# Create the OpenAI Agent with memory capabilities
agent = Agent(
    name="Memory-Enhanced Assistant",
    instructions=dedent("""
        You are a helpful AI assistant with the ability to remember past conversations
        and user preferences. You have access to two powerful memory functions:

        1. search_memory: Use this to search for relevant past conversations, user preferences,
           and any information from previous interactions. Always search your memory first
           when responding to questions about the user or past conversations.

        2. remember_user_info: Use this to store important information about the user
           such as their preferences, skills, interests, or goals for future reference.

        Guidelines:
        - Always start by searching your memory for relevant context before responding
        - When users share personal information, preferences, or important details,
          use remember_user_info to store it
        - Be conversational and personalize responses based on remembered information
        - If this is the first conversation, introduce yourself and explain your memory capabilities
        - Reference past conversations naturally when relevant

        Be helpful, friendly, and make use of your memory to provide personalized assistance.
    """),
    tools=[search_memory, remember_user_info],
)


async def chat_with_memory(user_input: str) -> str:
    """Process user input with memory-enhanced OpenAI Agent"""
    try:
        print(f"[debug] Processing user input: {user_input[:50]}...")

        # Run the agent with the user input
        result = await Runner.run(agent, input=user_input)

        # Get the response content
        response_content = (
            result.final_output if hasattr(result, "final_output") else str(result)
        )

        # Store the conversation in memory
        memory_system.record_conversation(
            user_input=user_input, ai_output=response_content
        )

        return response_content

    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        print(f"[debug] Error: {error_msg}")
        return error_msg


async def main():
    """Main interaction loop"""
    print("✅ Setup complete! Chat with your memory-enhanced OpenAI Agent.")
    print("Type 'quit', 'exit', or 'bye' to end the conversation.\n")

    print("💡 Try asking about:")
    print("- Your past conversations")
    print("- Share your preferences (I'll remember them!)")
    print("- Ask about topics we've discussed before")
    print("- Tell me about your interests or goals\n")

    conversation_count = 0

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            # Check for exit commands
            if user_input.lower() in ["quit", "exit", "bye"]:
                print(
                    "\nAI: Goodbye! I'll remember our conversation for next time. 🤖✨"
                )
                break

            if not user_input:
                continue

            conversation_count += 1
            print(f"\nAI (thinking... conversation #{conversation_count})")

            # Get response from memory-enhanced agent
            response = await chat_with_memory(user_input)

            print(f"AI: {response}\n")

        except KeyboardInterrupt:
            print("\n\nAI: Goodbye! I'll remember our conversation for next time. 🤖✨")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again.\n")

    print("\n📊 Session Summary:")
    print(f"- Conversations processed: {conversation_count}")
    print("- Memory database: openai_agent_memory.db")
    print("- Namespace: openai_agent_example")
    print("\nYour memories are saved and will be available in future sessions!")


if __name__ == "__main__":
    asyncio.run(main())
