import anthropic
from memori import Memori

# Initialize Memori with explicit recording
claude_memory = Memori(
    database_connect="sqlite:///claude_memory_explicit.db",
    conscious_ingest=True,  # Enable memory processing
)
claude_memory.enable()

# Create client
client = anthropic.Anthropic()

# Test conversations
test_inputs = [
    "Hello, my name is Test User and I'm testing explicit recording",
    "What is my name?",
    "I work on the Memori project"
]

for user_input in test_inputs:
    print(f"User: {user_input}")
    
    # Get response
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": user_input}]
    )
    
    # Display response
    if response.content:
        ai_text = "".join(b.text for b in response.content if hasattr(b, 'text'))
        print(f"AI: {ai_text}")
    
    # Simple explicit recording - just pass the response object
    chat_id = claude_memory.record_conversation(user_input, response)
    print(f"Recorded: {chat_id}")
    print("-" * 50)