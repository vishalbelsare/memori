# Digital Ocean AI + GibsonAI Memori Integration

Memory-enhanced customer support AI Agent using [Digital Ocean's Gradient platform](https://www.digitalocean.com/products/gradient/platform) with persistent conversation memory and intelligent context injection.

## Overview

This example demonstrates:
- Digital Ocean's Gradient platform platform integration with Memori
- Memory-enhanced customer support interactions
- Persistent conversation history across sessions
- Automatic context injection for personalized responses
- Professional customer support workflow

## Code

```python title="digital_ocean_example.py"
"""
Digital Ocean + GibsonAI Memori Integration Example

A memory-enhanced AI customer support assistant using Digital Ocean's AI platform
with Memori for persistent conversation memory and context-aware responses.

Requirements:
- pip install memorisdk openai python-dotenv
- Digital Ocean AI platform credentials
- Set OPENAI_API_KEY for memory processing
"""

import os

import openai
from dotenv import load_dotenv

from memori import Memori, create_memory_tool

# Load environment variables
load_dotenv()

# Check for required Digital Ocean credentials
agent_endpoint = os.getenv("agent_endpoint")
agent_access_key = os.getenv("agent_access_key")

if not agent_endpoint or not agent_access_key:
    print("❌ Error: Digital Ocean AI credentials not found in environment variables")
    print("Please set your Digital Ocean AI credentials:")
    print("export agent_endpoint='your-agent-endpoint-here'")
    print("export agent_access_key='your-agent-access-key-here'")
    print("or create a .env file with these values")
    exit(1)

print("🧠 Initializing Memori memory system...")

# Initialize Memori for persistent memory with Digital Ocean namespace
memory_system = Memori(
    database_connect="sqlite:///digital_ocean_memory.db",
    conscious_ingest=True,  # Enable AI-powered background analysis
    verbose=False,  # Set to True to see memory operations
    namespace="digital_ocean_support",  # Separate namespace for Digital Ocean interactions
)

# Enable the memory system
memory_system.enable()

# Create memory tool for potential function calling (future enhancement)
memory_tool = create_memory_tool(memory_system)

print("🤖 Setting up Digital Ocean AI client...")

# Configure Digital Ocean AI endpoint
base_url = (
    agent_endpoint
    if agent_endpoint.endswith("/api/v1/")
    else f"{agent_endpoint}/api/v1/"
)

# Initialize Digital Ocean AI client
client = openai.OpenAI(
    base_url=base_url,
    api_key=agent_access_key,
)


def create_memory_search_function(memori_tool):
    """Create a memory search function for potential function calling integration"""

    def search_customer_memory(query: str) -> str:
        """Search customer interaction history and support context.

        Args:
            query: What to search for in customer history (e.g., "past issues", "preferences", "technical problems")
        """
        try:
            if not query.strip():
                return "Please provide a search query for customer history"

            result = memori_tool.execute(query=query.strip())
            return str(result) if result else "No relevant customer history found"

        except Exception as e:
            return f"Customer history search error: {str(e)}"

    return search_customer_memory


def chat_with_memory(user_input: str, model: str = "n/a") -> str:
    """Process customer input with memory-enhanced Digital Ocean AI"""
    try:
        # Check memory for relevant customer context
        customer_context = ""
        if len(user_input.strip()) > 5:  # Only search for substantial queries
            try:
                context_result = memory_tool.execute(
                    query=user_input[:100]
                )  # Search with truncated query
                if (
                    context_result
                    and "No relevant memories found" not in context_result
                ):
                    customer_context = f"\n\nPrevious customer context:\n{context_result[:500]}..."  # Truncate context
            except Exception:
                pass  # Continue without context if search fails

        # Prepare enhanced prompt with customer context
        enhanced_input = user_input
        if customer_context:
            enhanced_input = f"{user_input}\n\n[Internal context from previous interactions: {customer_context}]"

        # Get response from Digital Ocean AI
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful customer support assistant. Use any previous interaction context to provide personalized and informed responses. Be friendly, professional, and solution-oriented.",
                },
                {"role": "user", "content": enhanced_input},
            ],
        )

        ai_response = response.choices[0].message.content

        # Record the conversation in memory (store original user input, not enhanced)
        memory_system.record_conversation(
            user_input=user_input,
            ai_output=ai_response,
            model=model,
            metadata={
                "platform": "digital_ocean",
                "interaction_type": "customer_support",
                "had_context": bool(customer_context),
            },
        )

        return ai_response

    except Exception as e:
        error_msg = f"Sorry, I encountered an error processing your request: {str(e)}"
        # Still try to record the error interaction
        try:
            memory_system.record_conversation(
                user_input=user_input,
                ai_output=error_msg,
                model=model,
                metadata={"platform": "digital_ocean", "error": True},
            )
        except:
            pass  # Don't let memory errors cascade
        return error_msg


# Main interaction loop
print("✅ Setup complete! Memory-enhanced Digital Ocean AI customer support is ready.")
print("Type 'quit', 'exit', or 'bye' to end the session.\n")

print("💡 As a customer support assistant, I can help with:")
print("- Technical support and troubleshooting")
print("- Account and billing questions")
print("- Product information and guidance")
print("- Service recommendations")
print("- I'll remember our conversation to provide better personalized support!\n")

conversation_count = 0

while True:
    try:
        # Get customer input
        user_input = input("Customer: ").strip()

        # Check for exit commands
        if user_input.lower() in ["quit", "exit", "bye"]:
            print(
                "\nSupport Agent: Thank you for contacting Digital Ocean support! I'll remember our conversation for future assistance. Have a great day! 🌊"
            )
            break

        if not user_input:
            continue

        conversation_count += 1
        print(f"\nSupport Agent (processing... interaction #{conversation_count})")

        # Get memory-enhanced response
        response = chat_with_memory(user_input)

        print(f"Support Agent: {response}\n")

    except KeyboardInterrupt:
        print(
            "\n\nSupport Agent: Thank you for contacting Digital Ocean support! I'll remember our conversation for future assistance. 🌊"
        )
        break
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please try again or type 'quit' to exit.\n")

print("\n📊 Digital Ocean Support Session Summary:")
print(f"- Customer interactions processed: {conversation_count}")
print("- Memory database: digital_ocean_memory.db")
print("- Namespace: digital_ocean_support")
print("- Agent endpoint:", agent_endpoint)
print("\nCustomer history is saved and will be available in future support sessions!")

# Optional: Trigger conscious analysis for better memory organization
if conversation_count > 2:
    try:
        print("\n🧠 Organizing conversation insights...")
        memory_system.trigger_conscious_analysis()
        print(
            "✅ Memory analysis complete - key insights saved for future interactions!"
        )
    except Exception as e:
        print(f"💡 Memory analysis will run in background: {e}")
```

## What Happens

### 1. Digital Ocean AI Integration
```python
base_url = agent_endpoint if agent_endpoint.endswith("/api/v1/") else f"{agent_endpoint}/api/v1/"

client = openai.OpenAI(
    base_url=base_url,
    api_key=agent_access_key,
)
```

**Digital Ocean Setup:**
- 🌊 **Endpoint Configuration**: Automatic `/api/v1/` suffix handling
- 🔐 **Credential Validation**: Checks for required environment variables
- 🔄 **OpenAI Compatibility**: Uses OpenAI client with Digital Ocean endpoints

### 2. Memory-Enhanced Support
```python
memory_system = Memori(
    database_connect="sqlite:///digital_ocean_memory.db",
    conscious_ingest=True,  # AI-powered analysis
    namespace="digital_ocean_support"  # Isolated memory space
)
```

**Memory Features:**
- 🧠 **Customer History**: Persistent conversation memory across sessions
- 🎯 **Context Injection**: Automatic retrieval of relevant previous interactions
- 📊 **Support Analytics**: Track interaction patterns and customer preferences
- 🔄 **Conscious Analysis**: Background processing identifies key customer information

### 3. Intelligent Context Retrieval
```python
context = search_memory(user_input)
enhanced_prompt = f"{context}\nCustomer: {user_input}" if context else user_input
```

**Context Intelligence:**
- 🔍 **Smart Search**: Vector-based search for relevant conversation history
- 💡 **Personalization**: Responses adapt based on customer's previous interactions
- 🎭 **Consistency**: Maintains context across support sessions
- 📈 **Learning**: System improves context selection over time

### 4. Professional Support Workflow
```python
messages=[
    {
        "role": "system",
        "content": """You are a helpful Digital Ocean customer support assistant..."""
    },
    {
        "role": "user", 
        "content": enhanced_prompt
    }
]
```

**Support Optimization:**
- 👥 **Professional Tone**: System prompt optimized for customer support
- 📋 **Context Awareness**: Previous conversations inform current responses
- 🔄 **Session Continuity**: Customers don't need to repeat information
- 📊 **Interaction Tracking**: Metadata for analytics and improvement

## Expected Output

```
🌊 Digital Ocean AI Customer Support with Memori
==================================================
✅ Memory system initialized for Digital Ocean support
🧠 Conscious ingestion enabled - conversations will be analyzed

🎯 Digital Ocean Customer Support Assistant Ready!
💡 I remember our previous conversations and your preferences
Type 'quit' to exit

Customer: I'm having issues with my droplet deployment
🔍 Retrieved relevant context from previous conversations

Support: I see you're having deployment issues. Based on our previous conversation about your Ubuntu 22.04 setup, let me help you troubleshoot...

💾 Conversation recorded in memory

Customer: My app keeps timing out
🔍 Retrieved relevant context from previous conversations

Support: Given your Node.js application we discussed earlier and the current timeout issues, this is likely related to...

💾 Conversation recorded in memory

Customer: quit

👋 Thank you for using Digital Ocean support!
📚 Conversation history saved (2 interactions)
🧠 Your context will be remembered for next time
```

## Database Contents

After running, check `digital_ocean_memory.db`:

### Memory Categories
- **Customer Info**: Account details, preferences, technical stack
- **Issues**: Historical problems and their resolutions
- **Solutions**: Successful troubleshooting steps
- **Preferences**: Communication style and technical complexity level

### Support Analytics
- **Interaction Patterns**: Common issue types and resolution paths
- **Customer Journey**: Support session flow and effectiveness
- **Context Usage**: How previous conversations inform current responses

## Setup and Configuration

### Step 1: Create a Digital Ocean Agent
Before setting up the integration, you need to create a new Agent on the DigitalOcean Gradient platform:

1. Follow the [DigitalOcean Gradient Platform Quickstart Guide](https://docs.digitalocean.com/products/gradient-platform/getting-started/quickstart/#create-agent) to create your agent
2. Note down your agent endpoint and access key from the agent configuration

### Step 2: Install Dependencies
```bash
pip install memorisdk openai python-dotenv
```

### Step 3: Configure Environment Variables

Create .env File

```env
# Digital Ocean AI credentials (from your created agent)
agent_endpoint=https://your-digital-ocean-endpoint.com
agent_access_key=your-digital-ocean-api-key
OPENAI_API_KEY=sk-your-openai-key-here
```

OR

```bash
# Digital Ocean AI credentials (from your created agent)
export agent_endpoint="https://your-digital-ocean-endpoint.com"
export agent_access_key="your-digital-ocean-api-key"

# OpenAI for memory processing
export OPENAI_API_KEY="sk-your-openai-key-here"
```

## Step 4: Run the Example

```bash
python digital_ocean_example.py
```

## Use Cases

### Customer Support Enhancement
- **Session Continuity**: Customers don't repeat information across sessions
- **Personalized Responses**: Adapt communication style to customer preferences
- **Issue Tracking**: Remember previous problems and solutions
- **Escalation Context**: Provide comprehensive history for complex issues

### Business Intelligence
- **Support Analytics**: Track common issues and resolution patterns
- **Customer Insights**: Understand user preferences and pain points
- **Quality Improvement**: Identify successful support strategies
- **Resource Optimization**: Focus training on frequently asked questions

## Advanced Features

### Custom Memory Search
```python
# Search for specific customer information
account_context = search_memory("account settings")
technical_context = search_memory("technical configuration")
```

### Metadata Tracking
```python
metadata={
    "platform": "digital_ocean",
    "interaction_type": "customer_support",
    "issue_category": "deployment",
    "resolution_status": "resolved"
}
```

### Memory Namespace Isolation
```python
# Separate memory spaces for different contexts
support_memory = Memori(namespace="digital_ocean_support")
billing_memory = Memori(namespace="digital_ocean_billing")
```

## Next Steps

- [Advanced Configuration](advanced-config.md) - Production deployment settings
- [Memory Optimization](memory-optimization.md) - Performance tuning
- [Integration Patterns](integration-patterns.md) - Multi-platform setups
- [API Reference](../api/core.md) - Complete Memori API documentation