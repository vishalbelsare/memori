"""
Test script for Memoriai v1.0 - Quick functionality check
"""

from memoriai import Memori, create_memory_search_tool
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    print("🧠 Testing Memoriai v1.0")
    print("=" * 30)
    
    # Initialize Memori with v1.0 architecture
    office_work = Memori(
        database_connect="sqlite:///test_memori.db",
        template="basic",
        mem_prompt="Focus on programming concepts and technical discussions",
        conscious_ingest=True,
        namespace="test_workspace",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    print("✅ Memori initialized")
    
    # Enable Pydantic-based processing
    office_work.enable()
    print("✅ Memori enabled with Pydantic processing!")
    
    # Test manual conversation recording
    print("\n📝 Testing conversation recording...")
    chat_id = office_work.record_conversation(
        user_input="What is the capital of France?",
        ai_output="The capital of France is Paris.",
        model="test-model"
    )
    
    print(f"✅ Conversation recorded with ID: {chat_id}")
    
    # Test memory retrieval
    print("\n🔍 Testing memory retrieval...")
    context = office_work.retrieve_context("France capital", limit=1)
    print(f"✅ Found {len(context)} relevant memories")
    
    if context:
        memory = context[0]
        print(f"   📄 Summary: {memory.get('summary', 'N/A')}")
        print(f"   📁 Category: {memory.get('category_primary', 'N/A')}")
        print(f"   ⭐ Importance: {memory.get('importance_score', 0):.2f}")
    
    # Test memory search tool
    print("\n🔧 Testing memory search tool...")
    search_tool = create_memory_search_tool(office_work)
    search_result = search_tool("France", max_results=2)
    print("✅ Memory search tool working!")
    print(f"   📊 Search result preview: {search_result[:100]}...")
    
    # Get statistics
    stats = office_work.get_memory_stats()
    print(f"\n📈 Memory Statistics:")
    print(f"   💬 Chat History: {stats.get('chat_history_count', 0)}")
    print(f"   🧠 Total Memories: {stats.get('short_term_count', 0) + stats.get('long_term_count', 0)}")
    
    # Clean up
    office_work.disable()
    print("\n✅ Test completed successfully!")
    print("🎉 Memoriai v1.0 is working correctly!")

if __name__ == "__main__":
    main()

