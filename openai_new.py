from memori import Memori
from openai import OpenAI
# Note: The developer no longer needs to import OpenAI from the openai library at all.
openai = OpenAI()

# 1. Initialize and configure the Memori system.
# This object holds the configuration (DB path, modes, etc.) but does nothing active yet.
personal = Memori(
    database_connect="sqlite:///openai_memory_CI.db",
    conscious_ingest=True,
    verbose=True,
)

# 3. Use the client as a drop-in replacement for the original.
while True:
    user_input = input("You: ")
    response = personal.client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_input}]
    )
    print(response.choices[0].message.content)