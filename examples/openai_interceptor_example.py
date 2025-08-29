#!/usr/bin/env python3
"""
OpenAI Interceptor Usage Examples

This script demonstrates how to use the new MemoriOpenAIInterceptor
for seamless OpenAI integration with automatic conversation recording.

The interceptor uses OpenAI's official extension hooks to provide
transparent integration without monkey-patching.
"""

import os
import sys
import asyncio

# Add the parent directory to Python path for local testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memori import Memori


def example_basic_usage():
    """Basic usage example - most common use case."""
    print("🎯 Example 1: Basic Usage")
    print("-" * 50)
    
    # Initialize Memori with OpenAI API key
    memori = Memori(
        database_connect="sqlite:///openai_interceptor_demo.db",
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        conscious_ingest=True,  # Enable context injection
        verbose=True
    )
    
    # Enable memory recording
    memori.enable()
    
    # Create OpenAI client with automatic recording
    client = memori.create_openai_client()
    
    print(f"✅ Created interceptor client: {type(client)}")
    print(f"📝 Ready for API calls - conversations will be auto-recorded")
    
    # Example API call (uncomment if you have a valid API key):
    # try:
    #     response = client.chat.completions.create(
    #         model="gpt-3.5-turbo",
    #         messages=[
    #             {"role": "user", "content": "Hello! What's the weather like?"}
    #         ]
    #     )
    #     print(f"💬 Response: {response.choices[0].message.content}")
    #     print("✅ Conversation automatically recorded to memory!")
    # except Exception as e:
    #     print(f"❌ API call failed (expected without valid key): {e}")
    
    return client


def example_azure_openai():
    """Azure OpenAI integration example."""
    print("\n🔷 Example 2: Azure OpenAI Integration")
    print("-" * 50)
    
    # Initialize Memori with Azure configuration
    memori = Memori(
        database_connect="sqlite:///openai_interceptor_demo.db",
        api_type="azure",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4"),
        api_version="2024-02-01",
        api_key=os.getenv("AZURE_OPENAI_API_KEY", "your-azure-key-here"),
        auto_ingest=True  # Enable automatic context injection
    )
    
    memori.enable()
    
    # Create Azure OpenAI client
    client = memori.create_openai_client()
    
    print(f"✅ Created Azure interceptor client: {type(client)}")
    print(f"🔷 Configured for Azure OpenAI endpoint")
    
    return client


def example_provider_config():
    """Using ProviderConfig for advanced configuration."""
    print("\n⚙️ Example 3: Advanced Provider Configuration")
    print("-" * 50)
    
    from memori.core.providers import ProviderConfig
    
    # Create provider configuration
    config = ProviderConfig.from_openai(
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        model="gpt-4o",
        organization="your-org-id",
        timeout=30.0,
        max_retries=3
    )
    
    # Initialize Memori with provider config
    memori = Memori(
        database_connect="sqlite:///openai_interceptor_demo.db",
        provider_config=config,
        conscious_ingest=True
    )
    
    memori.enable()
    
    # Create client using the provider config
    client = memori.create_openai_client()
    
    print(f"✅ Created client with advanced configuration")
    print(f"⚙️ Model: {config.model}, Timeout: {config.timeout}s")
    
    return client


async def example_async_usage():
    """Async client usage example."""
    print("\n🔄 Example 4: Async Client Usage")
    print("-" * 50)
    
    # Initialize Memori
    memori = Memori(
        database_connect="sqlite:///openai_interceptor_demo.db",
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        auto_ingest=True
    )
    
    memori.enable()
    
    # Create interceptor and get async client
    interceptor = memori.create_openai_client()
    async_client = interceptor.async_client
    
    print(f"✅ Created async client: {type(async_client)}")
    print(f"🔄 Ready for async API calls")
    
    # Example async API call (uncomment if you have a valid API key):
    # try:
    #     response = await async_client.chat.completions.create(
    #         model="gpt-3.5-turbo",
    #         messages=[
    #             {"role": "user", "content": "What's 2+2?"}
    #         ]
    #     )
    #     print(f"💬 Async Response: {response.choices[0].message.content}")
    #     print("✅ Async conversation automatically recorded!")
    # except Exception as e:
    #     print(f"❌ Async API call failed (expected without valid key): {e}")
    
    return async_client


def example_direct_import():
    """Direct import and usage example."""
    print("\n🎯 Example 5: Direct Import Usage")
    print("-" * 50)
    
    from memori.integrations.openai_integration import (
        MemoriOpenAIInterceptor,
        create_openai_client,
        setup_openai_interceptor
    )
    
    # Initialize Memori
    memori = Memori(
        database_connect="sqlite:///openai_interceptor_demo.db",
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    memori.enable()
    
    # Method 1: Direct instantiation
    client1 = MemoriOpenAIInterceptor(
        memori, 
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    
    # Method 2: Using factory function
    client2 = create_openai_client(memori)
    
    # Method 3: Using setup function (auto-detects config)
    client3 = setup_openai_interceptor(memori)
    
    print(f"✅ Created client via direct instantiation: {type(client1)}")
    print(f"✅ Created client via factory function: {type(client2)}")  
    print(f"✅ Created client via setup function: {type(client3)}")
    
    return client1, client2, client3


def example_streaming_support():
    """Streaming responses example."""
    print("\n🌊 Example 6: Streaming Support")
    print("-" * 50)
    
    from memori.integrations.openai_integration import create_streaming_handler
    
    # Initialize Memori
    memori = Memori(
        database_connect="sqlite:///openai_interceptor_demo.db",
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    memori.enable()
    
    # Create client
    client = memori.create_openai_client()
    
    # Create streaming handler (for manual stream processing if needed)
    stream_handler = create_streaming_handler(memori)
    
    print(f"✅ Created client with streaming support")
    print(f"🌊 Stream handler available for advanced use cases")
    
    # Example streaming call (uncomment if you have a valid API key):
    # try:
    #     stream = client.chat.completions.create(
    #         model="gpt-3.5-turbo",
    #         messages=[{"role": "user", "content": "Count from 1 to 5"}],
    #         stream=True
    #     )
    #     
    #     print("💬 Streaming response:")
    #     for chunk in stream:
    #         if chunk.choices[0].delta.content:
    #             print(chunk.choices[0].delta.content, end='')
    #     print("\n✅ Streaming conversation recorded!")
    #     
    # except Exception as e:
    #     print(f"❌ Streaming call failed (expected without valid key): {e}")
    
    return client


def example_memory_features():
    """Demonstrate memory features with interceptor."""
    print("\n🧠 Example 7: Memory Features Integration")
    print("-" * 50)
    
    # Initialize Memori with memory features
    memori = Memori(
        database_connect="sqlite:///openai_interceptor_demo.db",
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        conscious_ingest=True,  # One-shot context injection
        namespace="demo_session",
        user_id="demo_user"
    )
    
    memori.enable()
    
    # Add some user context
    memori.update_user_context(
        current_projects=["AI integration", "Memory systems"],
        relevant_skills=["Python", "Machine Learning", "API Integration"],
        user_preferences=["Technical explanations", "Code examples"]
    )
    
    # Create client
    client = memori.create_openai_client()
    
    print(f"✅ Created client with memory features enabled")
    print(f"🧠 Context injection: Conscious Ingest")
    print(f"📊 Namespace: {memori.namespace}")
    print(f"👤 User ID: {memori.user_id}")
    
    # Simulate some memory data (normally this would come from previous conversations)
    try:
        memori.record_conversation(
            user_input="I'm working on integrating OpenAI with my Python app",
            ai_output="Great! I can help you with OpenAI Python integration. Let's start with the client setup...",
            model="gpt-4o",
            metadata={"source": "demo"}
        )
        print("✅ Added sample conversation to memory")
    except Exception as e:
        print(f"⚠️ Could not add sample conversation: {e}")
    
    # The client will now automatically inject relevant context into future conversations
    print("💡 Future API calls will include relevant memory context automatically")
    
    return client


def example_legacy_compatibility():
    """Legacy wrapper compatibility example."""
    print("\n🔄 Example 8: Legacy Compatibility")
    print("-" * 50)
    
    from memori.integrations.openai_integration import MemoriOpenAI
    
    # Initialize Memori
    memori = Memori(
        database_connect="sqlite:///openai_interceptor_demo.db",
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    memori.enable()
    
    # Create legacy wrapper (still works but deprecated)
    legacy_client = MemoriOpenAI(
        memori,
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    
    # Create new interceptor
    new_client = memori.create_openai_client()
    
    print(f"✅ Legacy wrapper still works: {type(legacy_client)}")
    print(f"✅ New interceptor recommended: {type(new_client)}")
    print(f"⚠️ Migration path: Replace MemoriOpenAI with create_openai_client()")
    
    return legacy_client, new_client


async def main():
    """Run all examples."""
    print("🚀 OpenAI Interceptor Examples")
    print("=" * 60)
    
    # Run all examples
    client1 = example_basic_usage()
    client2 = example_azure_openai()
    client3 = example_provider_config()
    
    # Async example
    async_client = await example_async_usage()
    
    # Direct import examples
    direct_clients = example_direct_import()
    
    # Streaming support
    stream_client = example_streaming_support()
    
    # Memory features
    memory_client = example_memory_features()
    
    # Legacy compatibility
    legacy_clients = example_legacy_compatibility()
    
    print("\n" + "=" * 60)
    print("🏁 All Examples Complete!")
    print("\n💡 Key Benefits of the New Interceptor:")
    print("   • Uses OpenAI's official extension hooks")
    print("   • Supports all OpenAI endpoints (chat, completions, etc.)")
    print("   • Works with sync and async clients")
    print("   • Handles Azure OpenAI seamlessly")
    print("   • Automatic context injection based on memory")
    print("   • Error handling that doesn't break OpenAI client")
    print("   • Drop-in replacement for standard OpenAI client")
    
    print("\n📚 Usage Recommendations:")
    print("   1. Use memori.create_openai_client() for simplest setup")
    print("   2. Enable conscious_ingest or auto_ingest for context")
    print("   3. Use ProviderConfig for advanced configurations")
    print("   4. Prefer interceptor over legacy wrapper classes")
    
    print(f"\n🗄️ Check database 'openai_interceptor_demo.db' for recorded conversations")


if __name__ == "__main__":
    asyncio.run(main())