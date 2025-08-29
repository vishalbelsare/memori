from openai import OpenAI
from memori import Memori

openai_memory = Memori(
    database_connect="sqlite:///openai_memory_CI.db",
    conscious_ingest=True,
    verbose=True,
)

openai_memory.enable()

client = OpenAI()

while 1:
    user_input = input("You: ")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": user_input
            }
        ]
    )
    print(response.choices[0].message.content)