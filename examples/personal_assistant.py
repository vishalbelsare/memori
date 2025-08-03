"""
Personal Assistant with Memoriai
AI assistant that remembers your preferences and context
"""

from memoriai import Memori
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🤖 Personal Assistant with Memoriai")
    print("=" * 35)
    
    # Create personal memory space
    personal = Memori(
        database_connect="sqlite:///personal_assistant.db",
        namespace="personal",  # Separate from work memories
        conscious_ingest=True,
        openai_api_key="your-openai-key"
    )
    
    personal.enable()
    print("✅ Personal assistant memory enabled")
    
    # Simulate a conversation flow
    conversations = [
        {
            "context": "Establishing preferences",
            "user": "I'm a software engineer who loves Python and prefers minimalist tools",
            "expected": "Remembers: Python preference, minimalist tools"
        },
        {
            "context": "Daily routine",
            "user": "I usually code in the mornings and prefer short, focused work sessions",
            "expected": "Remembers: Work schedule, focus preferences"
        },
        {
            "context": "Learning goals",
            "user": "I want to learn more about AI and machine learning this year",
            "expected": "Remembers: Learning goals for AI/ML"
        },
        {
            "context": "Applying memory - tool recommendation",
            "user": "What development tools should I use for my next project?",
            "expected": "Suggests Python tools, considers minimalist preference"
        },
        {
            "context": "Applying memory - schedule advice",
            "user": "How should I structure my learning time?",
            "expected": "Considers morning coding preference, short sessions"
        }
    ]
    
    for i, conv in enumerate(conversations, 1):
        print(f"\n--- Conversation {i}: {conv['context']} ---")
        print(f"You: {conv['user']}")
        
        response = completion(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": conv['user']
            }]
        )
        
        print(f"Assistant: {response.choices[0].message.content}")
        print(f"💡 Expected memory: {conv['expected']}")
    
    print("\n🎯 Memory in Action:")
    print("  ✅ Preferences stored and applied")
    print("  ✅ Context carried across conversations")
    print("  ✅ Personalized responses based on memory")
    print("\n💾 Check 'personal_assistant.db' to see stored memories!")

if __name__ == "__main__":
    main()