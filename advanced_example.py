#!/usr/bin/env python3
"""
Advanced example demonstrating all Memori features including:
1. Auto-recording with multiple LLM libraries
2. Memory tool for function calling
3. Manual recording and retrieval
4. Memory statistics and monitoring
"""

import os
from memoriai import Memori, create_memory_tool, record_conversation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def demonstrate_auto_recording():
    """Demonstrate automatic conversation recording"""
    print("=== Auto-Recording Demo ===")

    # Initialize Memori for a coding assistant
    coding_assistant = Memori(
        database_connect="sqlite:///coding_assistant.db",
        template="basic",
        mem_prompt="Focus on programming concepts, code examples, and technical discussions",
        conscious_ingest=True,
        namespace="coding_workspace",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Enable auto-recording
    coding_assistant.enable()
    print("✅ Auto-recording enabled")

    # Example with OpenAI (if available)
    try:
        import openai

        client = openai.OpenAI()

        print("\n🤖 Making OpenAI call (will be auto-recorded)...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "Explain Python list comprehensions with examples",
                }
            ],
        )
        print("✅ OpenAI response auto-recorded!")

    except ImportError:
        print("❌ OpenAI not installed")
    except Exception as e:
        print(f"❌ OpenAI example failed: {e}")

    # Example with LiteLLM (if available)
    try:
        from litellm import completion

        print("\n🤖 Making LiteLLM call (will be auto-recorded)...")
        response = completion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "What are Python decorators and how do they work?",
                }
            ],
        )
        print("✅ LiteLLM response auto-recorded!")

    except ImportError:
        print("❌ LiteLLM not installed")
    except Exception as e:
        print(f"❌ LiteLLM example failed: {e}")

    # Get statistics
    stats = coding_assistant.get_memory_stats()
    print(f"\n📊 Memory Stats: {stats}")

    coding_assistant.disable()
    return coding_assistant


def demonstrate_memory_tool(memori_instance):
    """Demonstrate memory tool functionality"""
    print("\n=== Memory Tool Demo ===")

    # Create memory tool
    memory_tool = create_memory_tool(memori_instance)

    # Get tool schema (for LLM function calling)
    schema = memory_tool.get_tool_schema()
    print(f"🔧 Tool Schema: {schema['name']} - {schema['description']}")

    # Manual recording via tool
    print("\n📝 Recording conversation via tool...")
    result = memory_tool.execute(
        action="record",
        user_input="How do I optimize a Python function for performance?",
        ai_output="To optimize Python function performance: 1) Use built-in functions when possible, 2) Minimize function calls in loops, 3) Use list comprehensions over loops, 4) Consider caching with functools.lru_cache, 5) Profile your code to identify bottlenecks.",
        model="gpt-4",
    )
    print(f"✅ {result.get('message', 'Recorded')}")

    # Retrieve context via tool
    print("\n🔍 Retrieving context via tool...")
    context_result = memory_tool.execute(
        action="retrieve", query="Python optimization performance", limit=3
    )
    print(f"✅ {context_result.get('message', 'Retrieved context')}")

    # Print retrieved context
    for i, context in enumerate(context_result.get("context", []), 1):
        print(f"  {i}. [{context['category']}] {context['content'][:100]}...")

    # Search memories via tool
    print("\n🔎 Searching memories via tool...")
    search_result = memory_tool.execute(action="search", query="decorators", limit=5)
    print(f"✅ {search_result.get('message', 'Search completed')}")

    # Get stats via tool
    print("\n📊 Getting stats via tool...")
    stats_result = memory_tool.execute(action="stats")
    if stats_result.get("success"):
        print(f"📈 Memory Stats: {stats_result['memory_stats']}")
        print(f"🔗 Integration Stats: {stats_result['integration_stats']}")


def demonstrate_decorator():
    """Demonstrate the recording decorator"""
    print("\n=== Decorator Demo ===")

    # Create a simple memori instance
    simple_memori = Memori(
        database_connect="sqlite:///decorator_test.db",
        template="basic",
        conscious_ingest=False,  # Disable for simple demo
    )
    simple_memori.enable()

    # Create a mock LLM function
    @record_conversation(simple_memori)
    def mock_llm_call(messages, model="test-model"):
        """Mock LLM function for demonstration"""

        # Simulate LLM response
        class MockChoice:
            def __init__(self, content):
                self.message = type("obj", (object,), {"content": content})()

        class MockResponse:
            def __init__(self, content):
                self.choices = [MockChoice(content)]

        # Return mock response
        return MockResponse("This is a mock AI response about the user's question.")

    print("🎭 Calling decorated function...")
    response = mock_llm_call(
        messages=[{"role": "user", "content": "Tell me about Python"}], model="gpt-test"
    )
    print("✅ Function call completed and conversation recorded via decorator!")

    simple_memori.disable()


def demonstrate_multi_namespace():
    """Demonstrate multiple namespaces"""
    print("\n=== Multi-Namespace Demo ===")

    # Create memori instances for different projects
    web_project = Memori(
        database_connect="sqlite:///multi_project.db",
        namespace="web_development",
        mem_prompt="Focus on web development, HTML, CSS, JavaScript",
        conscious_ingest=True,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    ml_project = Memori(
        database_connect="sqlite:///multi_project.db",  # Same DB, different namespace
        namespace="machine_learning",
        mem_prompt="Focus on machine learning, data science, algorithms",
        conscious_ingest=True,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Enable both
    web_project.enable()
    ml_project.enable()

    # Record conversations in different namespaces
    web_project.record_conversation(
        user_input="How do I center a div in CSS?",
        ai_output="To center a div: use flexbox with justify-content: center and align-items: center, or use CSS Grid with place-items: center.",
        model="gpt-4",
    )

    ml_project.record_conversation(
        user_input="What is the difference between supervised and unsupervised learning?",
        ai_output="Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data.",
        model="gpt-4",
    )

    # Retrieve context from each namespace
    web_context = web_project.retrieve_context("CSS centering", limit=2)
    ml_context = ml_project.retrieve_context("learning algorithms", limit=2)

    print(f"🌐 Web namespace memories: {len(web_context)}")
    print(f"🤖 ML namespace memories: {len(ml_context)}")

    # Get stats for each namespace
    web_stats = web_project.get_memory_stats()
    ml_stats = ml_project.get_memory_stats()

    print(f"📊 Web project stats: {web_stats}")
    print(f"📊 ML project stats: {ml_stats}")

    web_project.disable()
    ml_project.disable()


def main():
    """Run all demonstrations"""
    print("🧠 Memori Advanced Examples")
    print("=" * 50)

    # Auto-recording demo
    memori_instance = demonstrate_auto_recording()

    # Memory tool demo
    demonstrate_memory_tool(memori_instance)

    # Decorator demo
    demonstrate_decorator()

    # Multi-namespace demo
    demonstrate_multi_namespace()

    print("\n🎉 All demos completed!")
    print("\nTip: Check the generated SQLite files to see the stored memories:")
    print("  - office_work.db")
    print("  - coding_assistant.db")
    print("  - decorator_test.db")
    print("  - multi_project.db")


if __name__ == "__main__":
    main()
