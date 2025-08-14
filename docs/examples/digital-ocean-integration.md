# Digital Ocean AI + Memori Integration

Memory-enhanced customer support assistant using Digital Ocean's AI platform with persistent conversation memory and intelligent context injection.

## Overview

This example demonstrates:
- Digital Ocean AI platform integration with Memori
- Memory-enhanced customer support interactions
- Persistent conversation history across sessions
- Automatic context injection for personalized responses
- Professional customer support workflow

## Code

```python title="digital_ocean_example.py"
"""
Digital Ocean + Memori Integration Example

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

load_dotenv()

def main():
    print("🌊 Digital Ocean AI Customer Support with Memori")
    print("=" * 50)
    
    # Validate credentials
    agent_endpoint = os.getenv("agent_endpoint")
    agent_access_key = os.getenv("agent_access_key")
    
    if not agent_endpoint or not agent_access_key:
        print("❌ Error: Missing Digital Ocean credentials!")
        print("Please set agent_endpoint and agent_access_key in your .env file")
        return
    
    # Initialize Digital Ocean memory system
    try:
        memory_system = Memori(
            database_connect="sqlite:///digital_ocean_memory.db",
            conscious_ingest=True,  # Enable AI-powered background analysis
            verbose=True,
            openai_api_key=None,  # Uses OPENAI_API_KEY from environment
            namespace="digital_ocean_support"  # Isolated memory space
        )
        memory_system.enable()
        print("✅ Memory system initialized for Digital Ocean support")
        print("🧠 Conscious ingestion enabled - conversations will be analyzed")
    except Exception as e:
        print(f"⚠️ Memory initialization failed: {e}")
        print("Continuing without memory features...")
        memory_system = None
    
    # Setup Digital Ocean AI client
    base_url = agent_endpoint if agent_endpoint.endswith("/api/v1/") else f"{agent_endpoint}/api/v1/"
    
    client = openai.OpenAI(
        base_url=base_url,
        api_key=agent_access_key,
    )
    
    # Create memory search function
    def create_memory_search_function():
        if not memory_system:
            return lambda query: ""
        
        memory_tool = create_memory_tool(memory_system)
        
        def search_memory_context(query):
            try:
                context = memory_tool.invoke({"query": query})
                return f"\n--- Previous Context ---\n{context}\n--- End Context ---\n" if context.strip() else ""
            except Exception as e:
                print(f"⚠️ Memory search failed: {e}")
                return ""
        
        return search_memory_context
    
    search_memory = create_memory_search_function()
    conversation_count = 0
    
    print("\n🎯 Digital Ocean Customer Support Assistant Ready!")
    print("💡 I remember our previous conversations and your preferences")
    print("Type 'quit' to exit\n")

    while True:
        user_input = input("Customer: ")
        
        if user_input.lower() == 'quit':
            print("\n👋 Thank you for using Digital Ocean support!")
            if memory_system and conversation_count > 0:
                print(f"📚 Conversation history saved ({conversation_count} interactions)")
                print("🧠 Your context will be remembered for next time")
            break
        
        conversation_count += 1
        
        try:
            # Get relevant context from memory
            context = search_memory(user_input)
            had_context = bool(context.strip())
            
            # Create enhanced prompt with context
            if context:
                enhanced_prompt = f"{context}\nCustomer: {user_input}"
                print("🔍 Retrieved relevant context from previous conversations")
            else:
                enhanced_prompt = user_input
            
            # Get response from Digital Ocean AI
            response = client.chat.completions.create(
                model="n/a",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful Digital Ocean customer support assistant. 
                        Use any provided context from previous conversations to give personalized, 
                        consistent responses. Be professional, helpful, and reference previous 
                        interactions when relevant."""
                    },
                    {
                        "role": "user", 
                        "content": enhanced_prompt
                    }
                ]
            )
            
            bot_response = response.choices[0].message.content
            print(f"\nSupport: {bot_response}\n")
            
            # Record the conversation in memory
            if memory_system:
                try:
                    memory_system.record_conversation(
                        user_message=user_input,
                        assistant_message=bot_response,
                        metadata={
                            "platform": "digital_ocean",
                            "interaction_type": "customer_support",
                            "conversation_number": conversation_count,
                            "had_context": had_context
                        }
                    )
                    print("💾 Conversation recorded in memory")
                except Exception as e:
                    print(f"⚠️ Memory recording failed: {e}")
        
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            print(f"\nSupport: {error_msg}\n")
            
            # Record error interactions too
            if memory_system:
                try:
                    memory_system.record_conversation(
                        user_message=user_input,
                        assistant_message=error_msg,
                        metadata={
                            "platform": "digital_ocean",
                            "interaction_type": "error",
                            "error": str(e)
                        }
                    )
                except:
                    pass

if __name__ == "__main__":
    main()
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

### Prerequisites
```bash
pip install memorisdk openai python-dotenv
```

### Environment Variables
```bash
# Digital Ocean AI credentials
export agent_endpoint="https://your-digital-ocean-endpoint.com"
export agent_access_key="your-digital-ocean-api-key"

# OpenAI for memory processing
export OPENAI_API_KEY="sk-your-openai-key-here"
```

### .env File
```env
agent_endpoint=https://your-digital-ocean-endpoint.com
agent_access_key=your-digital-ocean-api-key
OPENAI_API_KEY=sk-your-openai-key-here
```

## Running the Example

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