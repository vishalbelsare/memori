# Agno Framework Integration

Memory-enhanced AI agents using [Agno](https://github.com/agno-agi/agno) framework with persistent conversation memory and intelligent context injection.

## Overview

This example demonstrates:
- Agno framework integration with Memori
- Memory-enhanced AI agent conversations
- Persistent conversation history across sessions
- Automatic context retrieval for personalized responses
- Lightweight agent implementation with memory tools

## Code

```python title="agno_example.py"
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
```

## What Happens

### 1. Agno Agent Setup
```python
assistant_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[search_memory_tool],
    description="You are a helpful AI assistant with memory capabilities...",
)
```

**Agno Features:**
- 🤖 **Simple Agent Creation**: Clean, declarative agent configuration
- 🧠 **Memory Tool Integration**: Seamless tool addition with search capabilities
- 📝 **Flexible Instructions**: Clear agent behavior definition
- 🔧 **Model Flexibility**: Support for various OpenAI models

### 2. Memory-Enhanced Interactions
```python
memory_system = Memori(
    database_connect="sqlite:///agno_example_memory.db",
    conscious_ingest=True,  # AI-powered analysis
    namespace="agno_example"  # Isolated memory space
)
```

**Memory Features:**
- 🧠 **Conversation History**: Persistent memory across agent sessions
- 🎯 **Context Retrieval**: Automatic search for relevant past interactions
- 📊 **Memory Organization**: Background conscious analysis of conversations
- 🔄 **Session Continuity**: Agents remember user preferences and context

### 3. Tool-Based Memory Search
```python
def search_memory(query: str) -> str:
    """Search the agent's memory for past conversations and information."""
    result = memori_tool.execute(query=query.strip())
    return str(result) if result else "No relevant memories found"
```

**Search Intelligence:**
- 🔍 **Vector Search**: Semantic search through conversation history
- 💡 **Context Discovery**: Find relevant past conversations automatically
- 🎭 **Personalization**: Responses adapt based on previous interactions
- 📈 **Learning**: Memory system improves over time

### 4. Lightweight Integration
```python
response_content = str(result.content) if hasattr(result, "content") else str(result)
memory_system.record_conversation(user_input=user_input, ai_output=response_content)
```

**Integration Benefits:**
- ⚡ **Minimal Setup**: Simple integration with existing Agno workflows
- 📦 **Flexible Architecture**: Easy to adapt to different agent configurations
- 🔄 **Automatic Recording**: Conversations saved transparently
- 🎯 **Namespace Isolation**: Separate memory spaces for different use cases

## Expected Output

```
🧠 Initializing Memori memory system...
🤖 Creating memory-enhanced Agno agent...
✅ Setup complete! Chat with your memory-enhanced AI assistant.

💡 Try asking about:
- Your past conversations
- Your preferences  
- Previous topics discussed
- Any information you've shared before

You: Hi, I'm working on a Python machine learning project
AI (thinking... conversation #1)

AI: Hello! It's great to meet you. I'm an AI assistant with memory capabilities, which means I'll remember our conversations for future reference.

I'd love to help you with your Python machine learning project! To get started, could you tell me more about:
- What type of ML problem you're working on (classification, regression, etc.)
- Which libraries or frameworks you're using
- Any specific challenges you're facing

I'll remember all the details about your project so I can provide better assistance in future conversations!

You: I'm using scikit-learn for classification
AI (thinking... conversation #2) 
🔍 Retrieved relevant context from previous conversations

AI: Perfect! I remember you mentioned you're working on a Python machine learning project, and now I see it's a classification problem using scikit-learn. That's a great choice - scikit-learn has excellent classification algorithms.

For classification projects, you might want to consider:
- Which classifier to use (RandomForest, SVM, Logistic Regression, etc.)
- Feature preprocessing and selection
- Cross-validation strategies
- Performance metrics evaluation

What type of data are you classifying, and do you have any specific questions about your scikit-learn implementation?

💾 Conversation recorded in memory
```

## Database Contents

After running, check `agno_example_memory.db`:

### Memory Categories
- **Project Context**: Technical details about user's ML project
- **Preferences**: User's preferred libraries and approaches
- **Conversation Flow**: Natural progression of technical discussions
- **Problem-Solving History**: Solutions provided and their effectiveness

### Learning Patterns
- **Technical Focus Areas**: Machine learning, Python, specific frameworks
- **Question Types**: Implementation help, conceptual understanding
- **Solution Preferences**: Code examples, step-by-step guidance

## Setup and Configuration

### Step 1: Install Dependencies
```bash
pip install memorisdk agno python-dotenv
```

### Step 2: Configure Environment Variables
```bash
# Option 1: Environment variables
export OPENAI_API_KEY="sk-your-openai-key-here"

# Option 2: .env file
echo "OPENAI_API_KEY=sk-your-openai-key-here" > .env
```

### Step 3: Run the Example
```bash
python agno_example.py
```

## Use Cases

### Personal AI Assistant
- **Learning Companion**: Remember learning progress and preferences
- **Project Assistant**: Track multiple projects and their contexts
- **Conversation Continuity**: Pick up where previous sessions left off
- **Preference Learning**: Adapt communication style over time

### Development Support
- **Code Context**: Remember codebases and programming preferences
- **Technical Discussions**: Track solutions and their effectiveness
- **Learning Path**: Remember concepts learned and areas to improve
- **Debugging History**: Recall previous issues and their resolutions

## Advanced Features

### Custom Memory Queries
```python
# Search for specific technical information
tech_context = search_memory("machine learning algorithms discussed")
project_context = search_memory("Python project details")
```

### Agent Customization
```python
# Specialized agent with domain-specific memory
data_science_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[search_memory_tool],
    description="Data science specialist with memory of past analyses",
    instructions="Focus on statistical analysis and ML best practices"
)
```

### Memory Namespaces
```python
# Different memory spaces for different contexts
personal_memory = Memori(namespace="personal_assistant")
work_memory = Memori(namespace="work_projects")
learning_memory = Memori(namespace="learning_sessions")
```

## Next Steps

- [Advanced Memory Configuration](../configuration/settings.md) - Optimize memory performance
- [Multi-Agent Patterns](../examples/multi-agent-patterns.md) - Scale with multiple agents
- [Memory Analytics](../features.md#memory-analytics) - Analyze conversation patterns
- [API Reference](../api/core.md) - Complete Memori API documentation