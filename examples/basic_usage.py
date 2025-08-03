"""
Basic Memoriai Usage Example
Simple demonstration of memory recording and context injection
"""

from dotenv import load_dotenv
from litellm import completion

from memoriai import Memori

load_dotenv()


def main():
    print("🧠 Memoriai - Your AI's Second Memory")
    print("=" * 40)

    # Initialize your workspace memory
    office_work = Memori(
        database_connect="sqlite:///office_memory.db",
        conscious_ingest=True,  # Auto-inject relevant context
        openai_api_key="your-openai-key",  # Or set OPENAI_API_KEY in .env
    )

    # Enable memory recording
    office_work.enable()
    print("✅ Memory enabled - all conversations will be recorded!")

    # First conversation - establishing context
    print("\n--- First conversation ---")
    response1 = completion(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "I'm working on a FastAPI project with PostgreSQL database",
            }
        ],
    )
    print(f"Assistant: {response1.choices[0].message.content}")

    # Second conversation - memory automatically provides context
    print("\n--- Second conversation (with memory context) ---")
    response2 = completion(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Help me write database connection code"}
        ],
    )
    print(f"Assistant: {response2.choices[0].message.content}")

    # Third conversation - showing preference memory
    print("\n--- Third conversation (preferences remembered) ---")
    response3 = completion(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "I prefer clean, well-documented code with type hints",
            }
        ],
    )
    print(f"Assistant: {response3.choices[0].message.content}")

    # Fourth conversation - memory knows your preferences
    print("\n--- Fourth conversation (preferences applied) ---")
    response4 = completion(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Show me how to create a user model"}],
    )
    print(f"Assistant: {response4.choices[0].message.content}")

    print("\n🎉 That's it! Your AI now remembers your:")
    print("  • Tech stack (FastAPI, PostgreSQL)")
    print("  • Coding preferences (clean code, type hints)")
    print("  • Project context (user models, database connections)")
    print("\nNo more repeating context - just chat naturally!")


if __name__ == "__main__":
    main()
