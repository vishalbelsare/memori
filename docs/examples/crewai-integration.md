# CrewAI Framework Integration

Memory-enhanced multi-agent systems using [CrewAI](https://github.com/joaomdmoura/crewAI) framework with persistent conversation memory and intelligent context injection.

## Overview

This example demonstrates:
- CrewAI framework integration with Memori
- Memory-enhanced agent crews and task execution
- Persistent conversation history across crew sessions
- Tool-based memory search for intelligent context retrieval
- Professional multi-agent workflow with memory capabilities

## Code

```python title="crewai_example.py"
#!/usr/bin/env python3
"""
Lightweight CrewAI + Memori Integration Example

A minimal example showing how to integrate Memori memory capabilities
with CrewAI agents for persistent memory across conversations.

Requirements:
- pip install memorisdk crewai python-dotenv
- Set OPENAI_API_KEY in environment or .env file

Usage:
    python crewai.py
"""

import os

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
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
    database_connect="sqlite:///crewai_example_memory.db",
    conscious_ingest=True,
    verbose=False,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    namespace="crewai_example",
)

# Enable the memory system
memory_system.enable()

# Create memory tool for agents
memory_tool = create_memory_tool(memory_system)

print("🤖 Creating memory-enhanced CrewAI agent...")


# Create a memory search tool wrapper for agents
@tool("search_memory")
def search_memory(query: str) -> str:
    """Search the agent's memory for past conversations and information.

    Args:
        query: What to search for in memory (e.g., "past conversations about AI", "user preferences")
    """
    try:
        if not query.strip():
            return "Please provide a search query"

        result = memory_tool.execute(query=query.strip())
        return str(result) if result else "No relevant memories found"

    except Exception as e:
        return f"Memory search error: {str(e)}"


# Create an AI assistant agent with memory capabilities
assistant_agent = Agent(
    role="AI Assistant with Memory",
    goal="Help users while remembering past conversations and preferences",
    backstory="""You are a helpful AI assistant with the ability to remember past
    conversations and user preferences. Always check your memory first to provide
    personalized and contextual responses.""",
    tools=[search_memory],
    verbose=False,
    allow_delegation=False,
    max_iter=5,
)


def chat_with_memory(user_input: str) -> str:
    """Process user input with memory-enhanced agent"""

    # Create a task for the agent
    task = Task(
        description=f"""
        User says: "{user_input}"

        Instructions:
        1. First, search your memory for relevant past conversations using the search_memory tool
        2. Use any relevant memories to provide a personalized response
        3. Provide a helpful and contextual answer
        4. Be conversational and friendly

        If this is the first conversation, introduce yourself and explain that you'll remember our conversations.
        """,
        agent=assistant_agent,
        expected_output="A helpful, personalized response that considers past conversations",
    )

    # Create and run crew
    crew = Crew(
        agents=[assistant_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    # Execute the task
    result = crew.kickoff()

    # Store the conversation in memory
    memory_system.record_conversation(user_input=user_input, ai_output=str(result))

    return str(result)


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
print("- Memory database: crewai_example_memory.db")
print("- Namespace: crewai_example")
print("\nYour memories are saved and will be available in future sessions!")
```

## What Happens

### 1. CrewAI Agent Configuration
```python
assistant_agent = Agent(
    role="AI Assistant with Memory",
    goal="Help users while remembering past conversations and preferences",
    backstory="You are a helpful AI assistant with memory capabilities...",
    tools=[search_memory],
)
```

**CrewAI Features:**
- 👥 **Role-Based Agents**: Clear role definition with specific goals
- 🧠 **Tool Integration**: Seamless memory tool attachment
- 📋 **Structured Backstory**: Rich agent personality and capabilities
- 🔧 **Agent Configuration**: Fine-tuned behavior with delegation and iteration controls

### 2. Task-Driven Memory Integration
```python
task = Task(
    description=f"""User says: "{user_input}"
    Instructions: 1. First, search memory... 2. Use memories... 3. Provide response...""",
    agent=assistant_agent,
    expected_output="A helpful, personalized response that considers past conversations"
)
```

**Task Features:**
- 📝 **Clear Instructions**: Step-by-step memory integration workflow
- 🎯 **Expected Output**: Defined response quality expectations
- 🔄 **Memory-First Approach**: Always check memory before responding
- 💼 **Professional Structure**: Business-ready task execution

### 3. Crew Execution with Memory
```python
crew = Crew(
    agents=[assistant_agent],
    tasks=[task],
    process=Process.sequential,
    verbose=False,
)
result = crew.kickoff()
```

**Crew Management:**
- 🚀 **Crew Orchestration**: Managed agent and task execution
- 📊 **Process Control**: Sequential task processing with memory context
- 🔍 **Result Handling**: Clean extraction of agent responses
- 📈 **Scalability**: Easy extension to multi-agent crews

### 4. CrewAI Tool Integration
```python
@tool("search_memory")
def search_memory(query: str) -> str:
    """Search the agent's memory for past conversations and information."""
    result = memory_tool.execute(query=query.strip())
    return str(result) if result else "No relevant memories found"
```

**Tool Benefits:**
- 🛠️ **Native Tool Support**: CrewAI's decorator-based tool creation
- 🔍 **Semantic Search**: Vector-based memory retrieval
- 📚 **Context Discovery**: Intelligent conversation history search
- ⚡ **Performance**: Optimized memory querying

## Expected Output

```
🧠 Initializing Memori memory system...
🤖 Creating memory-enhanced CrewAI agent...
✅ Setup complete! Chat with your memory-enhanced AI assistant.

💡 Try asking about:
- Your past conversations
- Your preferences
- Previous topics discussed  
- Any information you've shared before

You: I need help planning a marketing campaign for my startup
AI (thinking... conversation #1)

AI: Hello! I'm your AI assistant with memory capabilities, which means I'll remember our conversations to provide better help over time.

I'd be happy to help you plan a marketing campaign for your startup! To create an effective strategy, I'll need to understand more about your business. Could you share:

- What industry/sector is your startup in?
- Who is your target audience?
- What's your current marketing budget range?
- What marketing channels have you tried before?
- What are your main goals for this campaign?

I'll remember all these details for future conversations, so you won't need to repeat them!

You: It's a SaaS product for small businesses, budget is around $5000
AI (thinking... conversation #2)
🔍 Retrieved relevant context from previous conversations

AI: Perfect! I remember you're working on a marketing campaign for your startup, and now I see it's a SaaS product targeting small businesses with a $5,000 budget. That's a solid foundation to work with.

For a SaaS product targeting small businesses with your budget, here's a strategic approach:

**Digital Marketing Focus ($5,000 budget):**
- **Content Marketing** ($1,500): Blog posts, case studies, how-to guides
- **Google Ads** ($2,000): Targeted search campaigns for business software keywords  
- **LinkedIn Ads** ($1,000): B2B targeting for small business owners
- **Email Marketing** ($300): Nurture sequences and onboarding
- **Tools & Analytics** ($200): Marketing automation and tracking

**Key questions to refine the strategy:**
- What specific business problem does your SaaS solve?
- How long is your typical sales cycle?
- Do you have existing customers for testimonials/case studies?

💾 Conversation recorded in memory
```

## Database Contents

After running, check `crewai_example_memory.db`:

### Memory Categories
- **Business Context**: Startup details, industry, target market
- **Campaign Planning**: Marketing strategies, budgets, timelines
- **User Preferences**: Communication style, decision-making patterns
- **Strategic Insights**: Successful approaches and lessons learned

### Crew Intelligence
- **Task Execution History**: How tasks were approached and completed
- **Agent Performance**: Response quality and user satisfaction
- **Context Utilization**: How memory influenced task outcomes
- **Workflow Patterns**: Common task sequences and flows

## Setup and Configuration

### Step 1: Install Dependencies
```bash
pip install memorisdk crewai python-dotenv
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
python crewai_example.py
```

## Use Cases

### Business Consulting
- **Strategic Planning**: Remember business context across planning sessions
- **Project Management**: Track project progress and decisions over time
- **Client Relations**: Maintain detailed client interaction history
- **Knowledge Management**: Build organizational memory for teams

### Content Creation Crews
- **Editorial Planning**: Remember content strategies and brand guidelines
- **Research Projects**: Track research findings and source materials
- **Creative Campaigns**: Maintain creative direction and feedback history
- **Publication Workflows**: Remember editorial calendars and deadlines

## Advanced Features

### Multi-Agent Memory Sharing
```python
# Create specialized agents that share memory
research_agent = Agent(
    role="Research Specialist",
    goal="Gather and analyze market intelligence",
    tools=[search_memory],
    backstory="Expert researcher with access to historical findings"
)

strategy_agent = Agent(
    role="Strategy Consultant", 
    goal="Develop actionable business strategies",
    tools=[search_memory],
    backstory="Strategic thinker who builds on past research and insights"
)

# Both agents access the same memory system
crew = Crew(
    agents=[research_agent, strategy_agent],
    tasks=[research_task, strategy_task],
    process=Process.sequential
)
```

### Complex Task Memory Integration
```python
market_research_task = Task(
    description="""
    Research the competitive landscape for SaaS tools in the small business market.
    
    Steps:
    1. Search memory for any previous market research or competitor analysis
    2. Identify key competitors and their positioning
    3. Analyze pricing strategies and feature comparisons
    4. Summarize findings with actionable insights
    """,
    agent=research_agent,
    expected_output="Comprehensive market analysis with competitive intelligence"
)
```

### Memory-Driven Crew Processes
```python
# Sequential process with memory continuity
sequential_crew = Crew(
    agents=[research_agent, analysis_agent, strategy_agent],
    tasks=[research_task, analysis_task, strategy_task],
    process=Process.sequential,  # Each agent builds on previous memory
)

# Hierarchical process with memory coordination  
hierarchical_crew = Crew(
    agents=[manager_agent, specialist_agents],
    process=Process.hierarchical,
    manager_llm=manager_llm,
    # Manager agent coordinates using shared memory
)
```

## Best Practices

### 1. **Memory-First Task Design**
Structure tasks to always check memory first:
```python
task_description = """
1. Search memory for relevant context using search_memory tool
2. Use retrieved context to inform your approach  
3. Complete the requested task with personalized insights
4. Provide actionable recommendations
"""
```

### 2. **Agent Specialization with Shared Memory**
Create domain-specific agents that share organizational memory:
```python
# Specialized agents with shared memory access
marketing_agent = Agent(role="Marketing Specialist", tools=[search_memory])
sales_agent = Agent(role="Sales Specialist", tools=[search_memory])  
product_agent = Agent(role="Product Specialist", tools=[search_memory])
```

### 3. **Error Handling and Fallbacks**
```python
try:
    result = crew.kickoff()
    memory_system.record_conversation(user_input, str(result))
except Exception as e:
    fallback_response = f"I encountered an issue but will remember this conversation: {e}"
    memory_system.record_conversation(user_input, fallback_response)
```

## Next Steps

- [Advanced Multi-Agent Patterns](../examples/multi-agent-patterns.md) - Complex crew configurations
- [Memory Optimization](../features.md#memory-optimization) - Performance tuning for crews
- [CrewAI Documentation](https://docs.crewai.com/) - Official CrewAI framework guide
- [API Reference](../api/core.md) - Complete Memori API documentation