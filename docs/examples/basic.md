# Basic Example

Simple demonstration of Memoriai's core functionality.

## Overview

This example shows how to:
- Initialize Memoriai with basic settings
- Enable universal memory recording
- See automatic context injection in action

## Code

```python title="basic_example.py"
from memoriai import Memori
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🧠 Memoriai - Your AI's Second Memory")
    
    # Initialize your workspace memory
    office_work = Memori(
        database_connect="sqlite:///office_memory.db",
        conscious_ingest=True,  # Auto-inject relevant context
        openai_api_key="your-openai-key"
    )
    
    # Enable memory recording
    office_work.enable()
    print("✅ Memory enabled - all conversations will be recorded!")
    
    # First conversation - establishing context
    print("\n--- First conversation ---")
    response1 = completion(
        model="gpt-4o-mini",
        messages=[{
            "role": "user", 
            "content": "I'm working on a FastAPI project with PostgreSQL database"
        }]
    )
    print(f"Assistant: {response1.choices[0].message.content}")
    
    # Second conversation - memory automatically provides context
    print("\n--- Second conversation (with memory context) ---")
    response2 = completion(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": "Help me write database connection code"
        }]
    )
    print(f"Assistant: {response2.choices[0].message.content}")
    
    # Third conversation - showing preference memory
    print("\n--- Third conversation (preferences remembered) ---")
    response3 = completion(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": "I prefer clean, well-documented code with type hints"
        }]
    )
    print(f"Assistant: {response3.choices[0].message.content}")
    
    print("\n🎉 That's it! Your AI now remembers your:")
    print("  • Tech stack (FastAPI, PostgreSQL)")  
    print("  • Coding preferences (clean code, type hints)")
    print("  • Project context (user models, database connections)")
    print("\nNo more repeating context - just chat naturally!")

if __name__ == "__main__":
    main()
```

## What Happens

### 1. Memory Initialization
```python
office_work = Memori(
    database_connect="sqlite:///office_memory.db",
    conscious_ingest=True,  # Key feature!
    openai_api_key="your-openai-key"
)
```

- Creates SQLite database for memory storage
- Enables intelligent context injection
- Sets up memory processing agent

### 2. Universal Recording
```python
office_work.enable()
```

- Activates universal LLM conversation recording
- Works with ANY LLM library (LiteLLM, OpenAI, Anthropic)
- Processes conversations with Pydantic-based intelligence

### 3. Context Injection
Each conversation builds on the previous:

1. **First**: Establishes tech stack (FastAPI, PostgreSQL)
2. **Second**: Provides FastAPI + PostgreSQL specific database help  
3. **Third**: Records code preferences
4. **Future**: All responses consider your preferences and context

## Expected Output

```
🧠 Memoriai - Your AI's Second Memory
✅ Memory enabled - all conversations will be recorded!

--- First conversation ---
Assistant: Great! FastAPI with PostgreSQL is an excellent stack for building modern APIs...

--- Second conversation (with memory context) ---  
Assistant: Since you're working with FastAPI and PostgreSQL, here's how to set up your database connection...

--- Third conversation (preferences remembered) ---
Assistant: I'll keep that in mind! Clean, well-documented code with type hints is definitely the way to go...

🎉 That's it! Your AI now remembers your:
  • Tech stack (FastAPI, PostgreSQL)
  • Coding preferences (clean code, type hints)  
  • Project context (user models, database connections)

No more repeating context - just chat naturally!
```

## Database Contents

After running, check `office_memory.db`:

### Tables Created
- `chat_history` - All conversations
- `short_term_memory` - Recent context  
- `long_term_memory` - Important insights
- `memory_entities` - Extracted entities (FastAPI, PostgreSQL, etc.)

### Memory Processing
Each conversation is processed to extract:
- **Entities**: FastAPI, PostgreSQL, code, type hints
- **Categories**: fact, preference, skill, context
- **Importance**: Scored for relevance and retention

## Running the Example

### Prerequisites
```bash
pip install memoriai python-dotenv
```

### Setup
```bash
# Set API key
export OPENAI_API_KEY="sk-your-key-here"

# Or create .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### Run
```bash
python basic_example.py
```

## Next Steps

- [Personal Assistant](personal-assistant.md) - AI that remembers your preferences
- [Advanced Config](advanced-config.md) - Production configuration
- [API Reference](../api/core.md) - Complete API documentation