import anthropic
from memori import Memori

claude_memory = Memori(
    database_connect="sqlite:///claude_memory2.db",
    auto_ingest=True,
    conscious_ingest=True,
    verbose=True,
)
claude_memory.enable()

client = anthropic.Anthropic()  # Use a single client instance

while True:
    user_input = input("You: ")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": user_input}
        ]
    )
    claude_memory.record(user_input,response)
    if hasattr(response, "content"):
        for block in response.content:
            if getattr(block, "type", None) == "text":
                print("AI:", getattr(block, "text", "No response text found"))
    else:
        print("AI: No response content found")

