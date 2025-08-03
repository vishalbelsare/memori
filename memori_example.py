from memoriai import Memori
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Create your workspace memory
office_work = Memori(
    database_connect="sqlite:///office_memory.db",
    conscious_ingest=True,  # Auto-inject relevant context
    verbose=True,  # Enable verbose logging
)

office_work.enable()  # Start recording conversations

# Use ANY LLM library - context automatically injected!
from litellm import completion

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting conversation. Goodbye!")
        break

    response = completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_input}]
    )
    print("AI:", response["choices"][0]["message"]["content"])