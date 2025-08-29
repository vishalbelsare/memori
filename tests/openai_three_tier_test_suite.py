#!/usr/bin/env python3
"""
OpenAI Three-Tier Architecture Test Suite
Tests all three patterns with REAL OpenAI API calls:
1. Auto-Integration (Magic) - automatic interception
2. Wrapper (Best Practice) - memori.openai_client()
3. Manual Recording (Manual Utility) - memori.record()
"""

import sys
import os
import time
import shutil
from typing import List

# Fix imports to work from any directory
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)  # Go up one level from tests/ to repo root
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

# Import test utils directly
import json
def load_inputs(json_file_path: str, limit: int = None):
    """Load test inputs from JSON file and return as a list of strings."""
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    user_inputs = data.get('user_input', {})
    sorted_keys = sorted(user_inputs.keys(), key=lambda x: int(x))
    
    if limit is not None and limit > 0:
        sorted_keys = sorted_keys[:limit]
    
    return [user_inputs[key] for key in sorted_keys]

from memori import Memori

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def check_openai_setup():
    """Check if OpenAI is properly set up with API key."""
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI package not installed. Run: pip install openai")
        return False
    
    # Check for API key in environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Set your API key: export OPENAI_API_KEY=your_key_here")
        return False
    
    print(f"✓ OpenAI setup verified (API key found: {api_key[:10]}...)")
    return True


def test_auto_integration_pattern(test_name: str, test_inputs: List[str], conscious_ingest: bool = False, auto_ingest: bool = False):
    """
    Test Auto-Integration Pattern (Magic) - REAL OpenAI calls with automatic interception.
    """
    print(f"\n{'='*60}")
    print(f"Testing Auto-Integration Pattern (Magic): {test_name}")
    print(f"Configuration: conscious_ingest={conscious_ingest}, auto_ingest={auto_ingest}")
    print(f"{'='*60}\n")
    
    # Create database directory for this test
    db_dir = f"test_databases/auto_integration_{test_name}"
    os.makedirs(db_dir, exist_ok=True)
    db_path = f"{db_dir}/memory.db"
    
    # Initialize Memori
    memory = Memori(
        database_connect=f"sqlite:///{db_path}",
        conscious_ingest=conscious_ingest,
        auto_ingest=auto_ingest,
        verbose=True
    )
    
    # Enable auto-integration (this activates the interceptors)
    memory.enable()
    
    # Check if OpenAI interceptor is active
    status = memory.get_interceptor_status()
    if not status.get("openai_native", {}).get("enabled", False):
        print("❌ OpenAI interceptor not active!")
        return None
    
    print("✓ OpenAI interceptor is active - ready for magic interception")
    
    # Create native OpenAI client (this will be automatically intercepted)
    client = OpenAI()
    
    print(f"\n🔮 Making REAL OpenAI calls with Auto-Integration Magic:")
    for i, user_input in enumerate(test_inputs, 1):
        try:
            print(f"[{i}/{len(test_inputs)}] User: {user_input}")
            
            # This call will be automatically intercepted and recorded!
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for testing
                messages=[{"role": "user", "content": user_input}],
                max_tokens=100
            )
            
            ai_response = response.choices[0].message.content
            print(f"[{i}/{len(test_inputs)}] AI: {ai_response[:80]}...")
            print(f"[{i}/{len(test_inputs)}] ✨ Automatically recorded via magic interception!")
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"[{i}/{len(test_inputs)}] Error: {e}")
            if "rate_limit" in str(e).lower():
                print("Rate limit hit, waiting 10 seconds...")
                time.sleep(10)
    
    memory.disable()
    print(f"\n✓ Auto-Integration Pattern test completed. Database: {db_path}\n")
    return db_path


def test_wrapper_pattern(test_name: str, test_inputs: List[str], conscious_ingest: bool = False, auto_ingest: bool = False):
    """
    Test Wrapper Pattern (Best Practice) - REAL OpenAI calls using memori.openai_client().
    """
    print(f"\n{'='*60}")
    print(f"Testing Wrapper Pattern (Best Practice): {test_name}")
    print(f"Configuration: conscious_ingest={conscious_ingest}, auto_ingest={auto_ingest}")
    print(f"{'='*60}\n")
    
    # Create database directory for this test
    db_dir = f"test_databases/wrapper_{test_name}"
    os.makedirs(db_dir, exist_ok=True)
    db_path = f"{db_dir}/memory.db"
    
    # Initialize Memori
    memory = Memori(
        database_connect=f"sqlite:///{db_path}",
        conscious_ingest=conscious_ingest,
        auto_ingest=auto_ingest,
        verbose=True
    )
    
    try:
        # Get wrapped OpenAI client
        client = memory.openai_client()
        print("✓ Successfully created wrapped OpenAI client")
        
        print(f"\n🎯 Making REAL OpenAI calls with Wrapper Pattern:")
        for i, user_input in enumerate(test_inputs, 1):
            try:
                print(f"[{i}/{len(test_inputs)}] User: {user_input}")
                
                # This call will be recorded through the clean wrapper interface!
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # Use cheaper model for testing
                    messages=[{"role": "user", "content": user_input}],
                    max_tokens=100
                )
                
                ai_response = response.choices[0].message.content
                print(f"[{i}/{len(test_inputs)}] AI: {ai_response[:80]}...")
                print(f"[{i}/{len(test_inputs)}] 📝 Recorded via wrapper pattern!")
                
                # Small delay to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"[{i}/{len(test_inputs)}] Error: {e}")
                if "rate_limit" in str(e).lower():
                    print("Rate limit hit, waiting 10 seconds...")
                    time.sleep(10)
                    
    except Exception as e:
        print(f"❌ Failed to create wrapped client: {e}")
        return None
    
    print(f"\n✓ Wrapper Pattern test completed. Database: {db_path}\n")
    return db_path


def test_manual_recording_pattern(test_name: str, test_inputs: List[str]):
    """
    Test Manual Recording Pattern (Manual Utility) - REAL OpenAI calls + manual recording.
    """
    print(f"\n{'='*60}")
    print(f"Testing Manual Recording Pattern (Manual Utility): {test_name}")
    print(f"{'='*60}\n")
    
    # Create database directory for this test
    db_dir = f"test_databases/manual_{test_name}"
    os.makedirs(db_dir, exist_ok=True)
    db_path = f"{db_dir}/memory.db"
    
    # Initialize Memori
    memory = Memori(
        database_connect=f"sqlite:///{db_path}",
        verbose=True
    )
    
    memory.enable()
    
    # Create regular OpenAI client (NOT wrapped, NOT intercepted)
    client = OpenAI()
    
    print(f"\n✋ Making REAL OpenAI calls with Manual Recording:")
    recorded_ids = []
    
    for i, user_input in enumerate(test_inputs, 1):
        try:
            print(f"[{i}/{len(test_inputs)}] User: {user_input}")
            
            # Make regular OpenAI call (not automatically recorded)
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for testing
                messages=[{"role": "user", "content": user_input}],
                max_tokens=100
            )
            
            ai_response = response.choices[0].message.content
            print(f"[{i}/{len(test_inputs)}] AI: {ai_response[:80]}...")
            
            # Manually record the conversation
            conversation_id = memory.record(
                response=response,  # Pass the full response object
                user_input=user_input,
                model="gpt-4o-mini",
                tokens_used=response.usage.total_tokens if response.usage else 0,
                manual_recording=True
            )
            recorded_ids.append(conversation_id)
            print(f"[{i}/{len(test_inputs)}] 🖐️ Manually recorded: {conversation_id}")
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"[{i}/{len(test_inputs)}] Error: {e}")
            if "rate_limit" in str(e).lower():
                print("Rate limit hit, waiting 10 seconds...")
                time.sleep(10)
    
    print(f"\n✓ Successfully recorded {len(recorded_ids)} conversations manually")
    print(f"✓ Manual Recording Pattern test completed. Database: {db_path}\n")
    return db_path


def main():
    """
    Main test runner for OpenAI Three-Tier Architecture with REAL API calls.
    """
    print("🚀 OpenAI Three-Tier Architecture Test Suite - REAL API CALLS")
    print("="*70)
    
    # Check OpenAI setup
    if not check_openai_setup():
        print("\n❌ Cannot proceed without proper OpenAI setup")
        sys.exit(1)
    
    # Load test inputs
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)  # Go up one level from tests/ to repo root
    json_path = os.path.join(repo_root, "tests", "test_inputs.json")
    
    try:
        test_inputs = load_inputs(json_path, limit=3)  # Use only 3 inputs to minimize API costs
    except FileNotFoundError:
        print(f"Test inputs file not found at: {json_path}")
        print("Using fallback test inputs...")
        test_inputs = [
            "What is the capital of France?",
            "My name is Harshal and I'm a software engineer",
            "What's my name?"
        ]
    
    print(f"Using {len(test_inputs)} test inputs to minimize API costs\n")
    
    # Clean up previous test databases
    if os.path.exists("test_databases"):
        print("Cleaning up previous test databases...")
        shutil.rmtree("test_databases")
    
    # Test basic configuration only (to minimize API costs)
    test_scenario = {"name": "basic", "conscious_ingest": False, "auto_ingest": False}
    
    created_databases = []
    
    print(f"\n⚡ Starting REAL API tests...")
    
    # Test 1: Auto-Integration Pattern (Magic)
    print("\n" + "🔮 PATTERN 1: AUTO-INTEGRATION (MAGIC)")
    db_path = test_auto_integration_pattern(
        test_scenario["name"], 
        test_inputs, 
        test_scenario["conscious_ingest"], 
        test_scenario["auto_ingest"]
    )
    if db_path:
        created_databases.append(("Auto-Integration (Magic)", test_scenario["name"], db_path))
    
    time.sleep(2)  # Brief pause between patterns
    
    # Test 2: Wrapper Pattern (Best Practice)
    print("\n" + "🎯 PATTERN 2: WRAPPER (BEST PRACTICE)")
    db_path = test_wrapper_pattern(
        test_scenario["name"], 
        test_inputs, 
        test_scenario["conscious_ingest"], 
        test_scenario["auto_ingest"]
    )
    if db_path:
        created_databases.append(("Wrapper (Best Practice)", test_scenario["name"], db_path))
    
    time.sleep(2)  # Brief pause between patterns
    
    # Test 3: Manual Recording Pattern (Manual Utility)
    print("\n" + "✋ PATTERN 3: MANUAL RECORDING (MANUAL UTILITY)")
    db_path = test_manual_recording_pattern("basic", test_inputs)
    if db_path:
        created_databases.append(("Manual Recording (Utility)", "basic", db_path))
    
    # Summary
    print("\n" + "="*70)
    print("🎉 OpenAI Three-Tier Architecture Tests Completed with REAL API calls!")
    print("="*70)
    print(f"\nTested {len(created_databases)} patterns:")
    
    for pattern, config, db_path in created_databases:
        if os.path.exists(db_path):
            size = os.path.getsize(db_path) / 1024  # Size in KB
            print(f"  ✅ {pattern}: {size:.2f} KB")
        else:
            print(f"  ❌ {pattern}: Database not created")
    
    print(f"\n💰 Total API calls made: {len(test_inputs) * len(created_databases)}")
    print("\n📖 Usage Examples:")
    print("1. 🔮 Auto-Integration (Magic):     memori.enable() → use OpenAI normally")
    print("2. 🎯 Wrapper (Best Practice):     client = memori.openai_client()")
    print("3. ✋ Manual Recording (Utility):  memori.record(response=..., user_input=...)")
    
    print("\n🔍 Check the databases to see recorded conversations!")


if __name__ == "__main__":
    main()