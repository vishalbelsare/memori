# LangChain Framework Integration

Memory-enhanced AI agents using [LangChain](https://github.com/langchain-ai/langchain) framework with persistent conversation memory and intelligent context injection.

## Overview

This example demonstrates:
- LangChain framework integration with Memori
- Memory-enhanced agent executors with persistent conversation history
- Custom tool integration for semantic memory search
- Professional agent workflows with context-aware responses
- Advanced prompt engineering with memory context

## Code

```python title="langchain_example.py"
#!/usr/bin/env python3
"""
Lightweight LangChain + Memori Integration Example

A minimal example showing how to integrate Memori memory capabilities
with LangChain agents for persistent memory across conversations.

Requirements:
- pip install memorisdk langchain==0.3.27 langchain-openai python-dotenv
- Set OPENAI_API_KEY in environment or .env file

Usage:
    python langchain_example.py
"""

import os
from typing import Optional, Type

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

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
    database_connect="sqlite:///langchain_example_memory.db",
    conscious_ingest=True,
    verbose=False,
    namespace="langchain_example",
)

# Enable the memory system
memory_system.enable()

# Create memory tool for agents
memory_tool = create_memory_tool(memory_system)

print("🤖 Creating memory-enhanced LangChain agent...")


class MemorySearchInput(BaseModel):
    """Input for the memory search tool."""

    query: str = Field(
        description="What to search for in memory (e.g., 'past conversations about AI', 'user preferences')"
    )


class MemorySearchTool(BaseTool):
    """LangChain tool for searching agent memory."""

    name: str = "search_memory"
    description: str = (
        "Search the agent's memory for past conversations and information. "
        "Use this to recall previous interactions, user preferences, and context."
    )
    args_schema: Type[BaseModel] = MemorySearchInput

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool to search memory."""
        try:
            if not query.strip():
                return "Please provide a search query"

            result = memory_tool.execute(query=query.strip())
            return str(result) if result else "No relevant memories found"

        except Exception as e:
            return f"Memory search error: {str(e)}"


# Create the memory search tool
memory_search_tool = MemorySearchTool()

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

# Create the prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful AI assistant with the ability to remember past
conversations and user preferences. Always check your memory first to provide
personalized and contextual responses.

Instructions:
1. First, search your memory for relevant past conversations using the search_memory tool
2. Use any relevant memories to provide a personalized response
3. Provide a helpful and contextual answer
4. Be conversational and friendly

If this is the first conversation, introduce yourself and explain that you'll remember our conversations.""",
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# Create the agent
agent = create_openai_tools_agent(llm, [memory_search_tool], prompt)

# Create the agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=[memory_search_tool],
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=5,
)


def chat_with_memory(user_input: str) -> str:
    """Process user input with memory-enhanced LangChain agent"""
    try:
        # Run the agent with the user input
        result = agent_executor.invoke(
            {
                "input": user_input,
                "chat_history": [],  # We're using Memori for persistent memory instead
            }
        )

        # Get the response content
        response_content = result.get(
            "output", "I apologize, but I couldn't generate a response."
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
print("- Memory database: langchain_example_memory.db")
print("- Namespace: langchain_example")
print("\nYour memories are saved and will be available in future sessions!")
```

## What Happens

### 1. LangChain Agent Architecture
```python
agent = create_openai_tools_agent(llm, [memory_search_tool], prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=[memory_search_tool],
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=5,
)
```

**LangChain Features:**
- 🤖 **OpenAI Tools Agent**: Advanced reasoning with tool integration
- 🛠️ **Custom Tool Support**: Seamless memory tool integration via BaseTool
- 🔄 **Agent Executor**: Robust execution with error handling and iteration limits
- 📝 **Prompt Templates**: Professional prompt engineering with placeholders

### 2. Professional Tool Architecture
```python
class MemorySearchTool(BaseTool):
    name: str = "search_memory"
    description: str = "Search the agent's memory for past conversations..."
    args_schema: Type[BaseModel] = MemorySearchInput
    
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        result = memory_tool.execute(query=query.strip())
        return str(result) if result else "No relevant memories found"
```

**Tool Benefits:**
- 🏗️ **Pydantic Integration**: Type-safe tool parameters with validation
- 📋 **Rich Descriptions**: Clear tool purpose for agent reasoning
- 🔧 **Error Handling**: Robust execution with graceful failures
- 📊 **Callback Support**: Integration with LangChain monitoring systems

### 3. Advanced Prompt Engineering
```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant with memory capabilities..."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
```

**Prompt Features:**
- 🧠 **Memory-First Instructions**: Clear memory integration workflow
- 📝 **Structured Templates**: Professional prompt organization
- 🔄 **Placeholder Support**: Flexible agent scratchpad integration
- 💬 **Chat History**: Traditional chat memory augmented with persistent memory

### 4. Enterprise-Ready Error Handling
```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=[memory_search_tool],
    verbose=False,
    handle_parsing_errors=True,  # Graceful error handling
    max_iterations=5,           # Prevent infinite loops
)
```

**Production Features:**
- ⚡ **Performance Control**: Iteration limits prevent runaway execution
- 🛡️ **Error Resilience**: Automatic parsing error recovery
- 📊 **Monitoring Support**: Optional verbose mode for debugging
- 🔒 **Controlled Execution**: Safe agent behavior in production

## Expected Output

```
🧠 Initializing Memori memory system...
🤖 Creating memory-enhanced LangChain agent...
✅ Setup complete! Chat with your memory-enhanced AI assistant.

💡 Try asking about:
- Your past conversations
- Your preferences
- Previous topics discussed
- Any information you've shared before

You: I'm learning Python and need help with data structures
AI (thinking... conversation #1)

AI: Hello! I'm your AI assistant with memory capabilities, which means I'll remember our conversations to help you better over time.

I'm excited to help you learn Python data structures! Python has several built-in data structures that are essential to master:

**Core Data Structures:**
- **Lists**: Ordered, mutable collections `[1, 2, 3]`
- **Tuples**: Ordered, immutable collections `(1, 2, 3)`  
- **Dictionaries**: Key-value pairs `{"key": "value"}`
- **Sets**: Unordered collections of unique items `{1, 2, 3}`

To give you the most helpful guidance:
- What's your current Python experience level?
- Are there specific data structures you're struggling with?
- What kind of projects are you working on?

I'll remember your learning preferences and progress for future conversations!

You: I understand lists but I'm confused about when to use dictionaries vs lists
AI (thinking... conversation #2)
🔍 Retrieved relevant context from previous conversations

AI: Great question! I remember you're learning Python data structures and already understand lists well. The choice between dictionaries and lists depends on how you need to access and organize your data.

**Use Lists when:**
- Order matters (first item, second item, etc.)
- You access items by position/index: `my_list[0]`
- You need to maintain sequence: `[step1, step2, step3]`
- Items can be duplicates: `[1, 1, 2, 3]`

**Use Dictionaries when:**
- You need fast lookup by a meaningful key
- You want to associate values with labels: `{"name": "Alice", "age": 30}`
- You need unique keys (no duplicates)
- Relationships matter more than order

**Example:**
```python
# List: Shopping items in order
shopping_list = ["bread", "milk", "eggs"]

# Dictionary: Student information  
student = {"name": "John", "grade": 85, "class": "CS101"}
```

Would you like me to show you more specific examples based on what type of projects you're working on?

💾 Conversation recorded in memory
```

## Database Contents

After running, check `langchain_example_memory.db`:

### Memory Categories
- **Learning Progress**: Topics covered, concepts understood, areas of confusion
- **Code Examples**: Snippets provided and their explanations
- **User Preferences**: Learning style, complexity level, preferred examples
- **Problem-Solving History**: Questions asked and solutions provided

### Agent Intelligence
- **Tool Usage Patterns**: How memory search influenced responses
- **Context Integration**: How past conversations shaped current answers
- **Learning Adaptation**: Evolution of explanations based on user progress
- **Conversation Flow**: Natural progression of learning topics

## Setup and Configuration

### Step 1: Install Dependencies
```bash
pip install memorisdk langchain==0.3.27 langchain-openai python-dotenv
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
python langchain_example.py
```

## Use Cases

### Educational AI Tutors
- **Personalized Learning**: Adapt teaching style to individual progress
- **Curriculum Continuity**: Remember concepts taught and build upon them
- **Progress Tracking**: Monitor learning milestones and knowledge gaps
- **Study Session Continuity**: Pick up where previous lessons ended

### Technical Support Systems
- **Issue Resolution**: Remember past problems and successful solutions
- **User Context**: Maintain technical environment and preference details
- **Escalation History**: Track complex issues across multiple interactions
- **Knowledge Base**: Build user-specific troubleshooting guides

## Advanced Features

### Multi-Tool Memory Integration
```python
# Combine memory search with other tools
tools = [
    memory_search_tool,
    web_search_tool,
    calculator_tool,
    code_execution_tool
]

agent = create_openai_tools_agent(llm, tools, prompt)
```

### Custom Memory Tool Extensions
```python
class DetailedMemoryTool(MemorySearchTool):
    """Extended memory tool with categorized search"""
    
    def _run(self, query: str, category: str = None) -> str:
        # Add category-specific memory search
        if category:
            result = memory_tool.execute(
                query=f"{category}: {query}",
                filters={"category": category}
            )
        else:
            result = memory_tool.execute(query=query)
        
        return str(result) if result else "No relevant memories found"
```

### RAG-Style Memory Integration
```python
# Combine document retrieval with conversation memory
class RAGMemoryAgent:
    def __init__(self, memory_system, document_retriever):
        self.memory = memory_system
        self.docs = document_retriever
        
    def enhanced_search(self, query: str):
        # Search both conversation memory and documents
        memory_context = self.memory.search(query)
        doc_context = self.docs.search(query)
        
        return f"Memory: {memory_context}\nDocs: {doc_context}"
```

### Chain-of-Thought with Memory
```python
memory_chain_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are an AI assistant with access to conversation memory.
    
    For each query:
    1. Search your memory for relevant context
    2. Think through the problem step by step
    3. Provide a detailed response with reasoning
    4. Explain how past conversations informed your answer
    """),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
```

## Best Practices

### 1. **Tool Description Optimization**
Write clear, specific tool descriptions for better agent reasoning:
```python
description = (
    "Search conversation memory for past interactions, user preferences, "
    "and contextual information. Use specific queries like 'user's programming "
    "experience' or 'previous discussions about databases' for best results."
)
```

### 2. **Error Handling and Fallbacks**
```python
def robust_memory_search(query: str) -> str:
    try:
        result = memory_tool.execute(query=query)
        return result if result else "No relevant memories found"
    except Exception as e:
        return f"Memory temporarily unavailable: {str(e)}"
```

### 3. **Performance Optimization**
```python
# Use specific memory queries to reduce search time
specific_queries = [
    "user's technical background",
    "recent code examples discussed", 
    "preferred programming languages"
]

# vs generic queries like "everything about the user"
```

## Next Steps

- [LangChain Documentation](https://python.langchain.com/) - Official LangChain framework guide
- [Advanced Agent Patterns](../examples/advanced-agents.md) - Complex agent architectures  
- [Memory Optimization](../features.md#memory-optimization) - Performance tuning for agents
- [API Reference](../api/core.md) - Complete Memori API documentation