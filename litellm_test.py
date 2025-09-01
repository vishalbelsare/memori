from litellm import completion

from memori import Memori

# Set up the SQLAlchemy engine for PostgreSQL
# engine_url = ""

litellm_memory = Memori(
    database_connect="sqlite:///testmemv2.db",
    conscious_ingest=True,
    auto_ingest=True,  # verbose=True,
    verbose=True,
)

litellm_memory.enable()

while 1:
    try:
        user_input = input("User: ")
        if not user_input.strip():
            continue
        response = completion(
            model="gpt-4o", messages=[{"role": "user", "content": user_input}]
        )
        print(f"AI: {response.choices[0].message['content']}")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        break
    except Exception as e:
        print(f"Error: {e}")
        continue
