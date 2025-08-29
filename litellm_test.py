from litellm import completion
from memori import Memori

litellm_memory = Memori(
    database_connect="sqlite:///patch-14.db",
    verbose=True,
)

litellm_memory.enable()

while 1:
    user_input = input("You: ")

    response = completion(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": user_input
            }
        ]
    )

    print("AI:", response.choices[0].message['content'])
