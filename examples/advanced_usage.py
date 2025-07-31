"""
Advanced usage example showing multi-agent memory sharing
"""

from memoriai import Memori
import uuid

def simulate_multi_agent_scenario():
    print("🤖 Multi-Agent Memory Sharing Example")
    print("=" * 45)
    
    # Shared memory database
    shared_db = "sqlite:///team_memory.db"
    team_namespace = "development_team"
    
    # Agent 1: Code Reviewer
    print("\n1. Setting up Code Reviewer Agent...")
    code_reviewer = Memori(
        database_connect=shared_db,
        template="basic",
        namespace=team_namespace,
        shared_memory=True,
        mem_prompt="Focus on code quality, standards, and best practices"
    )
    code_reviewer.enable()
    
    # Agent 2: Documentation Writer
    print("2. Setting up Documentation Writer Agent...")
    doc_writer = Memori(
        database_connect=shared_db,
        template="basic", 
        namespace=team_namespace,
        shared_memory=True,
        mem_prompt="Focus on documentation, explanations, and user guides"
    )
    doc_writer.enable()
    
    # Simulate team interactions
    print("\n3. Simulating team interactions...")
    
    # Code reviewer records code standards
    code_reviewer.record_conversation(
        user_input="What are our Python coding standards?",
        ai_output="We follow PEP 8 for Python code style, use type hints for all functions, and require 90% test coverage. All code must pass flake8 and mypy checks.",
        model="gpt-4"
    )
    
    # Documentation writer records project context
    doc_writer.record_conversation(
        user_input="Tell me about our current project structure",
        ai_output="We're building a Flask API with a React frontend. The backend handles user authentication, data processing, and serves a REST API. We use PostgreSQL for data storage.",
        model="gpt-4"
    )
    
    # Both agents can access shared memory
    print("\n4. Checking shared memory access...")
    
    # Code reviewer accessing shared history
    reviewer_history = code_reviewer.get_conversation_history(limit=10)
    print(f"   Code Reviewer sees {len(reviewer_history)} shared conversations")
    
    # Doc writer accessing shared history  
    doc_history = doc_writer.get_conversation_history(limit=10)
    print(f"   Doc Writer sees {len(doc_history)} shared conversations")
    
    # Memory stats for the team
    print("\n5. Team Memory Statistics:")
    team_stats = code_reviewer.get_memory_stats()
    for key, value in team_stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 45)
    print("✅ Multi-agent memory sharing working!")

def demonstrate_custom_filters():
    print("\n🎯 Custom Memory Filters Example")
    print("=" * 35)
    
    # Create selective memory system
    selective_memory = Memori(
        database_connect="sqlite:///selective_memory.db",
        template="basic",
        mem_prompt="Only remember important coding solutions and bug fixes",
        conscious_ingest=True,
        memory_filters={
            "include_keywords": ["error", "bug", "solution", "fix", "important"],
            "exclude_keywords": ["weather", "joke", "casual"],
            "min_importance": 0.6
        }
    )
    selective_memory.enable()
    
    # Test different types of input
    test_inputs = [
        ("This is a critical bug fix for the authentication system", "High importance - should be remembered"),
        ("What's the weather like today?", "Should be filtered out"),
        ("Here's an important solution for the database connection issue", "Should be remembered"),
        ("Just a casual conversation about lunch", "Should be filtered out")
    ]
    
    print("\nTesting memory filters:")
    for user_input, expected in test_inputs:
        chat_id = selective_memory.record_conversation(
            user_input=user_input,
            ai_output="Response to: " + user_input,
            model="gpt-4"
        )
        print(f"   Input: {user_input[:40]}...")
        print(f"   Expected: {expected}")
        print()
    
    stats = selective_memory.get_memory_stats()
    print(f"Total conversations recorded: {stats.get('chat_history_count', 0)}")
    print("✅ Selective memory filtering demonstrated!")

if __name__ == "__main__":
    simulate_multi_agent_scenario()
    demonstrate_custom_filters()
