"""
Ollama + Memori Interactive Chat
Simple demo of Memori working with local LLMs via Ollama
"""

from openai import OpenAI
from memori import Memori

print("🦙 Ollama + Memori Chat")
print("Commands: 'help', 'stats', 'exit'\n")

# Initialize Memori with Ollama
memori = Memori(
    database_connect="sqlite:///ollama_memory.db",
    base_url='http://localhost:11434/v1',
    api_key='ollama',
    model="harshalmore31/naval-gemma",
    conscious_ingest=True,
    namespace="ollama_chat"
)

memori.enable()
print("✅ Memori enabled\n")

# Create OpenAI client pointing to Ollama
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'
)

conversation_history = []

# Interactive conversation loop
while True:
    try:
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() in ["exit", "quit", "bye"]:
            break
            
        if user_input.lower() == "help":
            print("Commands:")
            print("  'stats' - Show memory statistics")
            print("  'clear' - Clear conversation history") 
            print("  'exit' - Quit")
            continue
            
        if user_input.lower() == "stats":
            stats = memori.get_memory_stats()
            print(f"Total memories: {stats.get('total_memories', 0)}")
            continue
            
        if user_input.lower() == "clear":
            conversation_history.clear()
            print("✅ History cleared")
            continue
        
        # Build messages with history
        messages = [{"role": "system", "content": "You are a helpful assistant. Be concise."}]
        messages.extend(conversation_history[-10:])  # Last 10 messages
        messages.append({"role": "user", "content": user_input})
        
        # Make API call (Memori intercepts automatically)
        response = client.chat.completions.create(
            model="harshalmore31/naval-gemma",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        ai_response = response.choices[0].message.content
        print(f"Assistant: {ai_response}")
        
        # Update history
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": ai_response})
            
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Ollama is running: 'ollama serve'")
        break

# Cleanup
memori.disable()
print("✅ Done")
