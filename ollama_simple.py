import os
import sys

# Add parent directory to path for memori import if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from openai import OpenAI  # noqa: E402

from memori import Memori  # noqa: E402

# Configure Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

print("🦙 Ollama Chat with Simple Memori Storage")
print(f"📍 Server: {OLLAMA_BASE_URL}")
print(f"🤖 Model: {OLLAMA_MODEL}")
print("💬 Type 'exit' or press Ctrl+C to quit")
print("-" * 50)

# Initialize Memori with MINIMAL configuration (no AI agents)
ollama_memory = Memori(
    database_connect="sqlite:///ollama_simple.db",
    conscious_ingest=False,  # Disable AI-powered memory processing
    auto_ingest=False,  # Disable AI-powered context injection
    verbose=False,  # Reduce logs
    # Don't configure AI agents - just store conversations
)

ollama_memory.enable()

# Initialize OpenAI client for Ollama
client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama",
)

print("✅ Simple conversation storage enabled (no AI memory processing)")

# Conversation loop
conversation_history = []

while True:
    try:
        user_input = input("\n👤 User: ")

        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("👋 Goodbye!")
            break

        if not user_input.strip():
            continue

        # Add to conversation history
        conversation_history.append({"role": "user", "content": user_input})

        # Keep conversation manageable
        if len(conversation_history) > 16:
            conversation_history = conversation_history[-16:]

        # Get response from Ollama
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Remember information from our conversation context.",
                }
            ]
            + conversation_history,
            max_tokens=250,
            temperature=0.7,
        )

        ai_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_response})

        print(f"🤖 AI: {ai_response}")

        # Small delay to ensure conversation is recorded
        import time

        time.sleep(0.1)

    except (EOFError, KeyboardInterrupt):
        print("\n\n👋 Exiting...")
        break
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg:
            print("❌ Connection error: Check if Ollama is running")
            break
        elif "model not found" in error_msg:
            print(f"❌ Model '{OLLAMA_MODEL}' not found")
            print(f"💡 Install with: ollama pull {OLLAMA_MODEL}")
            break
        else:
            print(f"❌ Error: {e}")
            continue

# Show final statistics
try:
    stats = ollama_memory.get_memory_stats()
    print("\n" + "=" * 50)
    print("📊 Session Statistics:")
    print(f"   Conversations stored: {stats.get('chat_history_count', 0)}")
    print("   Note: AI memory processing disabled in this version")
    print("=" * 50)
except Exception as e:
    print(f"Could not retrieve stats: {e}")

print("\n💾 Conversations saved to: ollama_simple.db")

# Disable memory
ollama_memory.disable()
