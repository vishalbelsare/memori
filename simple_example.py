#!/usr/bin/env python3
"""
Simple example demonstrating Memori auto-recording functionality
"""

import os
from memoriai import Memori
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Initialize Memori with your preferences
    office_work = Memori(
        database_connect="sqlite:///office_work.db",
        template="basic",
        mem_prompt="Only record {python} related stuff!",
        conscious_ingest=True,
        openai_api_key=os.getenv("OPENAI_API_KEY")  # Optional: will use env var if not provided
    )
    
    # Enable auto-recording (installs hooks into LLM libraries)
    office_work.enable()
    
    print("Memori enabled! Now any LLM calls will be automatically recorded.")
    print(f"Session ID: {office_work.session_id}")
    print(f"Namespace: {office_work.namespace}")
    
    # Example: Manual conversation recording
    chat_id = office_work.record_conversation(
        user_input="What is function calling in Python?",
        ai_output="Function calling in Python is a type of tool that allows LLMs to go beyond generating text. It enables the model to execute specific functions with structured parameters, making AI agents more capable of performing tasks like API calls, calculations, and data manipulation.",
        model="gpt-4"
    )
    
    print(f"Recorded conversation: {chat_id}")
    
    # Example: Auto-recording with LiteLLM (if installed)
    try:
        from litellm import completion
        
        print("\nMaking LiteLLM call (will be auto-recorded)...")
        response = completion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "Explain Python decorators in simple terms"
                }
            ]
        )
        
        print("LiteLLM response received and automatically recorded!")
        
    except ImportError:
        print("LiteLLM not installed, skipping auto-recording example")
    except Exception as e:
        print(f"LiteLLM example failed: {e}")
    
    # Retrieve context
    print("\nTesting memory retrieval...")
    context = office_work.retrieve_context("Python function", limit=3)
    print(f"Found {len(context)} relevant memories")
    
    for i, item in enumerate(context, 1):
        print(f"{i}. {item.get('content', '')[:100]}...")
    
    # Get memory statistics
    stats = office_work.get_memory_stats()
    print(f"\nMemory Statistics: {stats}")
    
    # Get integration statistics
    integration_stats = office_work.get_integration_stats()
    print(f"Integration Statistics: {integration_stats}")
    
    # Disable auto-recording
    office_work.disable()
    print("\nMemori disabled.")

if __name__ == "__main__":
    main()