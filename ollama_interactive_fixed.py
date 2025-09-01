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
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")  # Try a larger model

print("🦙 Ollama Interactive Chat with Memori (FIXED)")
print(f"📍 Server: {OLLAMA_BASE_URL}")
print(f"🤖 Model: {OLLAMA_MODEL}")
print("💬 Type 'exit' or press Ctrl+C to quit")
print("-" * 50)

# IMPORTANT: Set environment variables to force ALL agents to use Ollama
os.environ["OPENAI_API_KEY"] = "ollama"  # Dummy key
os.environ["OPENAI_BASE_URL"] = OLLAMA_BASE_URL  # Force OpenAI client to use Ollama

print("🔧 Configured environment to force memory agents to use Ollama")

# Initialize Memori with explicit Ollama configuration
ollama_memory = Memori(
    database_connect="sqlite:///ollama_fixed.db",
    conscious_ingest=False,  # Disable conscious ingest for now
    auto_ingest=False,  # Disable auto-ingest for now
    verbose=True,
    # Explicit Ollama configuration
    base_url=OLLAMA_BASE_URL,
    model=OLLAMA_MODEL,
    api_key="ollama",
    # Force the provider configuration
    api_type="openai_compatible",  # This should help identify it as non-OpenAI
)

ollama_memory.enable()

# Initialize OpenAI client for Ollama
client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama",  # required, but unused by Ollama
)

print("✅ Memori initialized - memory agents should now use Ollama")

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

        # Keep conversation history manageable (last 10 exchanges)
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        # Get response from Ollama using OpenAI client
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Remember information about the user from our conversation.",
                }
            ]
            + conversation_history,
            max_tokens=300,
            temperature=0.7,
        )

        ai_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_response})

        print(f"🤖 AI: {ai_response}")

    except (EOFError, KeyboardInterrupt):
        print("\n\n👋 Exiting...")
        break
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg:
            print(f"❌ Connection error: Cannot connect to Ollama at {OLLAMA_BASE_URL}")
            print("💡 Make sure Ollama is running: 'ollama serve'")
            break
        elif "model not found" in error_msg or "404" in error_msg:
            print(f"❌ Model '{OLLAMA_MODEL}' not found")
            print(f"💡 Install it with: ollama pull {OLLAMA_MODEL}")
            break
        elif "rate limit" in error_msg:
            print(
                "❌ Rate limit hit - this means memory agents are still using OpenAI!"
            )
            print("💡 Check OpenAI API configuration")
            break
        else:
            print(f"❌ Error: {e}")
            continue

# Show final statistics
try:
    stats = ollama_memory.get_memory_stats()
    print("\n" + "=" * 50)
    print("📊 Session Memory Statistics:")
    print(f"   Long-term memories: {stats.get('long_term_count', 0)}")
    print(f"   Chat history entries: {stats.get('chat_history_count', 0)}")
    print("=" * 50)
except Exception as e:
    print(f"Could not retrieve memory stats: {e}")

print("\n💾 Conversation saved to: ollama_fixed.db")

# Disable memory
ollama_memory.disable()
