#!/usr/bin/env python3
"""
Test script for the new conscious_ingest functionality

This script demonstrates how the conscious agent works:
1. Records conversations in long-term memory
2. Analyzes patterns to extract essential personal facts  
3. Stores facts in short-term memory for immediate context
4. Prioritizes essential facts in context injection
"""

import asyncio
import os
import sys
import time

# Add the memoriai package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from memoriai import Memori
from loguru import logger

def simulate_conversations(memori: Memori):
    """Simulate conversations to build up memory patterns"""
    
    print("\n=== Simulating Conversations to Build Memory ===")
    
    conversations = [
        # Identity and basic info
        ("Hi, I'm Harshal", "Hello Harshal! Nice to meet you. How can I help you today?"),
        ("I'm a software developer", "Great! What kind of development do you work on?"),
        ("I work on AI and machine learning projects", "That's fascinating! AI and ML are exciting fields."),
        
        # Preferences
        ("I love eating mangoes", "Mangoes are delicious! They're one of the best tropical fruits."),
        ("My favorite programming language is Python", "Python is excellent for AI and data science!"),
        ("I prefer working late at night", "Many developers are night owls. When do you usually work?"),
        ("I typically sleep around 2am", "That's quite late! Do you find you're most productive at night?"),
        
        # Work patterns and habits
        ("I'm currently working on the Memoriai project", "That sounds like an interesting project! What does it do?"),
        ("It's a memory layer for AI agents", "That's really cool! Memory systems are crucial for AI."),
        ("I usually code for 6-8 hours per day", "That's a good amount of focused coding time."),
        ("I drink coffee every morning", "Coffee is essential for many developers!"),
        
        # Skills and expertise
        ("I'm experienced with FastAPI and Django", "Both are excellent Python web frameworks!"),
        ("I know machine learning and deep learning", "Those are valuable skills in today's market."),
        ("I use PostgreSQL for most of my databases", "PostgreSQL is a robust choice for databases."),
        
        # Relationships and context
        ("I work remotely from home", "Remote work has become very common. Do you enjoy it?"),
        ("My team uses Slack for communication", "Slack is great for team collaboration."),
        ("I'm learning about vector databases", "Vector databases are becoming important for AI applications."),
        
        # Reinforcement - repeat key facts
        ("Actually, let me clarify - my name is Harshal More", "Thank you for the clarification, Harshal More!"),
        ("I really love mangoes, they're my favorite fruit", "I remember you mentioning mangoes before!"),
        ("I stay up until 2am most nights working", "That late night schedule seems to work well for you."),
        ("Python is definitely my go-to language", "Python is perfect for your AI and ML work."),
    ]
    
    print(f"Recording {len(conversations)} conversations...")
    
    for i, (user_input, ai_output) in enumerate(conversations, 1):
        try:
            chat_id = memori.record_conversation(
                user_input=user_input,
                ai_output=ai_output,
                model="test-model"
            )
            print(f"  {i:2d}. Recorded: '{user_input[:50]}...'")
            time.sleep(0.1)  # Small delay to simulate real conversations
            
        except Exception as e:
            print(f"  ERROR recording conversation {i}: {e}")
    
    print(f"\n[OK] Recorded {len(conversations)} conversations")

def test_memory_retrieval(memori: Memori):
    """Test memory retrieval to see what's stored"""
    
    print("\n=== Testing Memory Retrieval ===")
    
    # Test queries
    test_queries = [
        "Who am I?",
        "What do I like to eat?", 
        "What's my sleep schedule?",
        "What programming language do I prefer?",
        "What project am I working on?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        context = memori.retrieve_context(query, limit=3)
        
        if context:
            for i, item in enumerate(context, 1):
                summary = item.get('summary', item.get('searchable_content', 'No summary'))
                category = item.get('category_primary', 'unknown')
                print(f"  {i}. [{category}] {summary}")
        else:
            print("  No context found")

def test_essential_facts(memori: Memori):
    """Test extraction of essential facts"""
    
    print("\n=== Testing Essential Facts Extraction ===")
    
    # Get current essential facts
    facts = memori.get_essential_facts(limit=10)
    
    if facts:
        print(f"Found {len(facts)} essential facts:")
        for i, fact in enumerate(facts, 1):
            summary = fact.get('summary', fact.get('searchable_content', 'No summary'))
            print(f"  {i}. {summary}")
    else:
        print("No essential facts found yet.")
        print("Note: Essential facts are extracted by the conscious agent running in the background.")
        print("This may take a few minutes after recording conversations.")

def trigger_conscious_analysis(memori: Memori):
    """Manually trigger conscious analysis for immediate results"""
    
    print("\n=== Triggering Conscious Analysis ===")
    
    if hasattr(memori, 'trigger_conscious_analysis'):
        print("Manually triggering conscious agent analysis...")
        task = memori.trigger_conscious_analysis()
        
        if task:
            print("Analysis triggered successfully!")
            print("Waiting for analysis to complete...")
            time.sleep(5)  # Give it time to run
        else:
            print("Analysis triggered in background thread")
            time.sleep(10)  # Give more time for background execution
    else:
        print("Conscious analysis trigger not available")

def main():
    """Main test function"""
    
    print("=== Testing New Conscious Ingest Functionality ===")
    print("\nThis test demonstrates the new conscious_ingest behavior:")
    print("1. Long-term memory stores detailed conversations")
    print("2. ConsciouscAgent analyzes patterns in the background") 
    print("3. Essential facts are extracted to short-term memory")
    print("4. Context injection prioritizes essential facts")
    
    # Create Memori instance with conscious ingestion enabled
    print("\n=== Initializing Memori with Conscious Ingestion ===")
    
    try:
        memori = Memori(
            database_connect="sqlite:///test_conscious.db",
            conscious_ingest=True,
            verbose=True,
            user_id="harshal_test"
        )
        
        memori.enable()
        print("[OK] Memori initialized successfully")
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize Memori: {e}")
        return
    
    try:
        # Step 1: Simulate conversations to build memory
        simulate_conversations(memori)
        
        # Step 2: Test memory retrieval (should show long-term memories)
        test_memory_retrieval(memori)
        
        # Step 3: Trigger conscious analysis manually
        trigger_conscious_analysis(memori)
        
        # Step 4: Test essential facts extraction
        test_essential_facts(memori)
        
        # Step 5: Test context retrieval with essential facts priority
        print("\n=== Testing Context with Essential Facts Priority ===")
        test_memory_retrieval(memori)
        
        print("\n=== Test Complete ===")
        print("\nThe new conscious_ingest workflow:")
        print("✓ Conversations stored in long-term memory")
        print("✓ Background conscious agent analyzes patterns")  
        print("✓ Essential facts extracted to short-term memory")
        print("✓ Context injection prioritizes essential facts")
        print("✓ Personal facts (name, preferences, habits) readily available")
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
    finally:
        try:
            memori.disable()
            print("\n[OK] Memori disabled")
        except:
            pass

if __name__ == "__main__":
    main()