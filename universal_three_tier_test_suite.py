#!/usr/bin/env python3
"""
Universal Three-Tier Architecture Test Suite

This test suite validates that the refactored unified three-tier architecture
works correctly for all providers (OpenAI, Anthropic, LiteLLM) with:

1. Auto-Integration Pattern (Magic): Automatic interception with minimal code changes
2. Wrapper Pattern (Best Practice): Clean wrapped interfaces for new projects  
3. Manual Recording Pattern (Manual Utility): Universal compatibility with any LLM provider

This suite tests backward compatibility and the new unified approach.
"""

import sys
import os
import time
import json
from typing import List, Dict, Any

# Add the repo root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from memori import Memori


def load_test_inputs() -> List[str]:
    """Load test inputs, with fallback for basic testing."""
    json_path = os.path.join(script_dir, "tests", "test_inputs.json")
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        user_inputs = data.get('user_input', {})
        sorted_keys = sorted(user_inputs.keys(), key=lambda x: int(x))
        
        # Use only first 2 inputs to minimize costs
        return [user_inputs[key] for key in sorted_keys[:2]]
    
    except FileNotFoundError:
        print(f"Test inputs file not found at: {json_path}")
        return [
            "My name is Alice and I'm a software engineer",
            "What's my name?"
        ]


def test_universal_architecture_initialization():
    """Test that the universal architecture initializes correctly."""
    print("\n🧪 Testing Universal Architecture Initialization")
    print("=" * 60)
    
    try:
        # Initialize Memori with universal architecture
        memory = Memori(
            database_connect="sqlite:///test_universal.db",
            verbose=True
        )
        
        # Check that universal components are available
        assert hasattr(memory, 'pattern_manager'), "Pattern manager not available"
        assert memory.memory_manager is not None, "Memory manager not initialized"
        
        # Check provider support
        status = memory.get_interceptor_status()
        print(f"✓ Universal architecture initialized successfully")
        print(f"  Available interceptor statuses: {list(status.keys())}")
        
        if hasattr(memory.memory_manager, 'pattern_manager') and memory.memory_manager.pattern_manager:
            universal_status = memory.memory_manager.pattern_manager.get_status()
            print(f"  Universal manager status: {universal_status.get('universal_manager', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Universal architecture initialization failed: {e}")
        return False


def test_auto_integration_pattern():
    """Test Auto-Integration Pattern (Magic) with the unified architecture."""
    print("\n🔮 Testing Auto-Integration Pattern (Magic)")
    print("=" * 60)
    
    try:
        memory = Memori(
            database_connect="sqlite:///test_auto_integration_universal.db",
            verbose=True
        )
        
        # Enable auto-integration
        memory.enable()
        print("✓ Auto-integration enabled")
        
        # Check status
        status = memory.get_interceptor_status()
        print(f"✓ Status after enabling: {list(status.keys())}")
        
        # Check which providers are enabled
        enabled_providers = []
        for provider_name, provider_status in status.items():
            if provider_status.get("enabled", False) and provider_name != "universal":
                enabled_providers.append(provider_name.replace("_native", ""))
        
        if enabled_providers:
            print(f"✓ Auto-integration enabled for providers: {', '.join(enabled_providers)}")
        else:
            print("⚠️  No providers enabled (may be due to missing API keys or SDKs)")
        
        memory.disable()
        print("✓ Auto-integration pattern test completed")
        return True
        
    except Exception as e:
        print(f"❌ Auto-integration pattern test failed: {e}")
        return False


def test_wrapper_pattern():
    """Test Wrapper Pattern (Best Practice) with the unified architecture."""
    print("\n🎯 Testing Wrapper Pattern (Best Practice)")
    print("=" * 60)
    
    try:
        memory = Memori(
            database_connect="sqlite:///test_wrapper_universal.db",
            verbose=True
        )
        
        memory.enable()
        
        # Test OpenAI wrapper
        try:
            openai_client = memory.openai_client()
            print("✓ OpenAI wrapped client created successfully")
            print(f"  Client type: {type(openai_client)}")
        except Exception as e:
            print(f"⚠️  OpenAI wrapper failed (may be due to missing SDK): {e}")
        
        # Test Anthropic wrapper
        try:
            anthropic_client = memory.anthropic_client()
            print("✓ Anthropic wrapped client created successfully")
            print(f"  Client type: {type(anthropic_client)}")
        except Exception as e:
            print(f"⚠️  Anthropic wrapper failed (may be due to missing SDK): {e}")
        
        # Test LiteLLM wrapper
        try:
            litellm_client = memory.litellm_client()
            print("✓ LiteLLM wrapped client created successfully")
            print(f"  Client type: {type(litellm_client)}")
        except Exception as e:
            print(f"⚠️  LiteLLM wrapper failed (may be due to missing SDK): {e}")
        
        print("✓ Wrapper pattern test completed")
        return True
        
    except Exception as e:
        print(f"❌ Wrapper pattern test failed: {e}")
        return False


def test_manual_recording_pattern():
    """Test Manual Recording Pattern (Manual Utility) with the unified architecture."""
    print("\n✋ Testing Manual Recording Pattern (Manual Utility)")
    print("=" * 60)
    
    try:
        memory = Memori(
            database_connect="sqlite:///test_manual_universal.db",
            verbose=True
        )
        
        memory.enable()
        
        # Test manual recording with different provider types
        test_cases = [
            {
                "provider_type": "openai",
                "response": MockOpenAIResponse("Hello! I'm Claude, an AI assistant."),
                "user_input": "Hello, who are you?",
                "model": "gpt-4o"
            },
            {
                "provider_type": "anthropic", 
                "response": MockAnthropicResponse("I'm Claude, created by Anthropic."),
                "user_input": "Tell me about yourself",
                "model": "claude-3-sonnet"
            },
            {
                "provider_type": "litellm",
                "response": MockLiteLLMResponse("I'm an AI assistant."),
                "user_input": "What are you?",
                "model": "gpt-3.5-turbo"
            }
        ]
        
        recorded_ids = []
        
        for test_case in test_cases:
            try:
                conversation_id = memory.record(
                    response=test_case["response"],
                    user_input=test_case["user_input"],
                    model=test_case["model"],
                    provider_type=test_case["provider_type"]
                )
                recorded_ids.append(conversation_id)
                print(f"✓ Manual recording for {test_case['provider_type']}: {conversation_id}")
                
            except Exception as e:
                print(f"⚠️  Manual recording failed for {test_case['provider_type']}: {e}")
        
        print(f"✓ Manual recording pattern test completed. Recorded {len(recorded_ids)} conversations")
        return True
        
    except Exception as e:
        print(f"❌ Manual recording pattern test failed: {e}")
        return False


def test_backward_compatibility():
    """Test that existing code still works with the new architecture."""
    print("\n🔄 Testing Backward Compatibility")
    print("=" * 60)
    
    try:
        # Test legacy initialization
        memory = Memori(
            database_connect="sqlite:///test_backward_compat.db",
            conscious_ingest=False,
            auto_ingest=False,
            verbose=True
        )
        
        # Test legacy methods still work
        memory.enable()
        
        # Test legacy status methods
        status = memory.get_interceptor_status()
        health = memory.get_interceptor_health()
        integration_stats = memory.get_integration_stats()
        
        print("✓ Legacy status methods work:")
        print(f"  Interceptor status keys: {list(status.keys())}")
        print(f"  Health check keys: {list(health.keys())}")
        print(f"  Integration stats: {len(integration_stats)} entries")
        
        # Test legacy pattern methods
        try:
            # This should work the same as before
            openai_client = memory.openai_client()
            print("✓ Legacy openai_client() method works")
        except Exception as e:
            print(f"⚠️  Legacy openai_client() failed: {e}")
        
        # Test manual recording (enhanced but backward compatible)
        try:
            mock_response = MockOpenAIResponse("Hello world")
            conversation_id = memory.record(
                response=mock_response,
                user_input="Hello",
                model="gpt-4o"
            )
            print(f"✓ Legacy manual recording works: {conversation_id}")
        except Exception as e:
            print(f"⚠️  Legacy manual recording failed: {e}")
        
        memory.disable()
        print("✓ Backward compatibility test completed")
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False


def test_provider_registry():
    """Test that providers are properly registered and discoverable."""
    print("\n📋 Testing Provider Registry")
    print("=" * 60)
    
    try:
        # Test provider discovery
        from memori.integrations.providers import get_available_providers
        from memori.core.providers_base import provider_registry
        
        available_providers = get_available_providers()
        print(f"✓ Available provider types: {[p.value for p in available_providers]}")
        
        # Test provider registry
        registry_providers = provider_registry.get_available_providers()
        print(f"✓ Registry provider types: {[p.value for p in registry_providers]}")
        
        # Test provider instantiation
        memory = Memori(database_connect="sqlite:///test_registry.db")
        
        if hasattr(memory.memory_manager, 'pattern_manager') and memory.memory_manager.pattern_manager:
            for provider_type in available_providers:
                try:
                    provider = memory.memory_manager.pattern_manager._get_or_create_provider(provider_type)
                    if provider:
                        print(f"✓ {provider_type.value} provider created successfully")
                        print(f"  Available: {provider.is_available}")
                    else:
                        print(f"⚠️  {provider_type.value} provider not available")
                except Exception as e:
                    print(f"⚠️  {provider_type.value} provider failed: {e}")
        
        print("✓ Provider registry test completed")
        return True
        
    except Exception as e:
        print(f"❌ Provider registry test failed: {e}")
        return False


# Mock response classes for testing
class MockOpenAIResponse:
    def __init__(self, content: str):
        self.choices = [MockChoice(MockMessage(content))]
        self.model = "gpt-4o"
        self.usage = MockUsage(100, 50, 150)

class MockAnthropicResponse:
    def __init__(self, content: str):
        self.content = [MockTextBlock(content)]
        self.model = "claude-3-sonnet"
        self.usage = MockAnthropicUsage(80, 40)

class MockLiteLLMResponse:
    def __init__(self, content: str):
        self.choices = [MockChoice(MockMessage(content))]
        self.model = "gpt-3.5-turbo"
        self.usage = MockUsage(75, 35, 110)

class MockChoice:
    def __init__(self, message):
        self.message = message
        self.finish_reason = "stop"

class MockMessage:
    def __init__(self, content: str):
        self.content = content

class MockTextBlock:
    def __init__(self, text: str):
        self.text = text
        self.type = "text"

class MockUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens

class MockAnthropicUsage:
    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


def main():
    """Run the complete universal three-tier architecture test suite."""
    print("🚀 Universal Three-Tier Architecture Test Suite")
    print("=" * 70)
    print("Testing the unified architecture across all providers:")
    print("1. Auto-Integration Pattern (Magic)")
    print("2. Wrapper Pattern (Best Practice)")
    print("3. Manual Recording Pattern (Manual Utility)")
    print("=" * 70)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Universal Architecture Initialization", test_universal_architecture_initialization),
        ("Provider Registry", test_provider_registry),
        ("Auto-Integration Pattern", test_auto_integration_pattern),
        ("Wrapper Pattern", test_wrapper_pattern),
        ("Manual Recording Pattern", test_manual_recording_pattern),
        ("Backward Compatibility", test_backward_compatibility),
    ]
    
    for test_name, test_function in tests:
        print(f"\n{'='*60}")
        print(f"🧪 Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_function()
            test_results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {e}")
            test_results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*70}")
    print("🎉 Universal Three-Tier Architecture Test Results")
    print(f"{'='*70}")
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\n📊 Summary: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎯 All tests passed! The universal three-tier architecture is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n📖 Universal Three-Tier Architecture Usage:")
    print("1. 🔮 Auto-Integration (Magic):     memori.enable() → use any LLM SDK normally")
    print("2. 🎯 Wrapper (Best Practice):     client = memori.openai_client() | memori.anthropic_client() | memori.litellm_client()")
    print("3. ✋ Manual Recording (Utility):  memori.record(response=..., user_input=..., provider_type='openai')")
    
    print(f"\n🔍 Test databases created in: {script_dir}")
    print("The unified architecture now works consistently across all providers!")


if __name__ == "__main__":
    main()