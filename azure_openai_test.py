import os
import shutil
import sys
import time

from openai import AzureOpenAI

from memori import Memori

# Fix imports to work from any directory
script_dir = os.path.dirname(os.path.abspath(__file__))
tests_dir = os.path.dirname(script_dir)
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

from tests.utils.test_utils import load_inputs  # noqa: E402


def validate_azure_config():
    """
    Validate Azure OpenAI configuration from environment variables.
    Returns tuple (is_valid, config_dict)
    """
    config = {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    }

    is_valid = (
        config["api_key"]
        and config["endpoint"]
        and not config["api_key"].startswith("your-")
        and not config["endpoint"].startswith("https://your-")
    )

    return is_valid, config


def run_azure_test_scenario(
    test_name, conscious_ingest, auto_ingest, test_inputs, azure_config
):
    """
    Run an Azure OpenAI test scenario with specific configuration.

    Args:
        test_name: Name of the test scenario
        conscious_ingest: Boolean for conscious_ingest parameter
        auto_ingest: Boolean for auto_ingest parameter
        test_inputs: List of test inputs to process
        azure_config: Azure OpenAI configuration dictionary
    """
    print(f"\n{'='*60}")
    print(f"Running Azure OpenAI Test: {test_name}")
    print(
        f"Configuration: conscious_ingest={conscious_ingest}, auto_ingest={auto_ingest}"
    )
    print(f"Endpoint: {azure_config['endpoint']}")
    print(f"Deployment: {azure_config['deployment']}")
    print(f"{'='*60}\n")

    # Create database directory for this test
    db_dir = f"test_databases_azure_openai/{test_name}"
    os.makedirs(db_dir, exist_ok=True)
    db_path = f"{db_dir}/memory.db"

    # Initialize Memori with specific configuration
    memory = Memori(
        database_connect=f"sqlite:///{db_path}",
        conscious_ingest=conscious_ingest,
        auto_ingest=auto_ingest,
        verbose=True,
    )

    memory.enable()

    # Create Azure OpenAI client
    try:
        client = AzureOpenAI(
            azure_endpoint=azure_config["endpoint"],
            api_key=azure_config["api_key"],
            api_version=azure_config["api_version"],
        )

        # Test connection first
        print("🔍 Testing Azure OpenAI connection...")
        client.chat.completions.create(
            model=azure_config["deployment"],
            messages=[{"role": "user", "content": "Hello, this is a connection test."}],
            max_tokens=10,
        )
        print("✅ Azure OpenAI connection successful\n")

    except Exception as e:
        print(f"❌ Azure OpenAI connection failed: {e}")
        memory.disable()
        return False

    success_count = 0
    error_count = 0

    # Run test inputs
    for i, user_input in enumerate(test_inputs, 1):
        try:
            response = client.chat.completions.create(
                model=azure_config["deployment"],
                messages=[{"role": "user", "content": user_input}],
                max_tokens=500,
                temperature=0.7,
            )

            ai_response = response.choices[0].message.content
            print(f"[{i}/{len(test_inputs)}] User: {user_input}")
            print(f"[{i}/{len(test_inputs)}] AI: {ai_response[:100]}...")

            # Show token usage if available
            if hasattr(response, "usage") and response.usage:
                print(f"[{i}/{len(test_inputs)}] Tokens: {response.usage.total_tokens}")

            success_count += 1

            # Small delay to avoid rate limiting
            time.sleep(1)

        except Exception as e:
            print(f"[{i}/{len(test_inputs)}] Error: {e}")
            error_count += 1

            if "rate_limit" in str(e).lower() or "429" in str(e):
                print("Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
            elif "quota" in str(e).lower():
                print("Quota exceeded - stopping test")
                break
            else:
                # Continue with other inputs for other types of errors
                time.sleep(5)

    # Get memory statistics
    try:
        stats = memory.get_memory_stats()
        print("\n📊 Memory Statistics:")
        print(f"   Successful API calls: {success_count}")
        print(f"   Failed API calls: {error_count}")
        print(f"   Long-term memories: {stats.get('long_term_count', 'N/A')}")
        print(f"   Chat history entries: {stats.get('chat_history_count', 'N/A')}")
    except Exception as e:
        print(f"   Could not retrieve memory stats: {e}")

    # Disable memory after test
    memory.disable()

    print(f"\n✓ Azure OpenAI Test '{test_name}' completed.")
    print(f"  Database saved at: {db_path}")
    print(
        f"  Success rate: {success_count}/{len(test_inputs)} ({100*success_count/len(test_inputs):.1f}%)\n"
    )

    return success_count > 0


def main():
    """
    Main Azure OpenAI test runner.
    """
    # Validate Azure OpenAI configuration
    is_valid, azure_config = validate_azure_config()

    if not is_valid:
        print("❌ Azure OpenAI configuration invalid or missing!")
        print("\nRequired environment variables:")
        print("- AZURE_OPENAI_API_KEY")
        print("- AZURE_OPENAI_ENDPOINT")
        print("- AZURE_OPENAI_DEPLOYMENT_NAME (optional, defaults to 'gpt-4o')")
        print("- AZURE_OPENAI_API_VERSION (optional)")
        print("\nExample:")
        print("export AZURE_OPENAI_API_KEY='your-api-key'")
        print("export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("export AZURE_OPENAI_DEPLOYMENT_NAME='gpt-4-turbo'")
        print("\nSkipping Azure OpenAI tests...")
        return False

    # Load test inputs
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.path.dirname(script_dir)
    json_path = "test_inputs.json"
    test_inputs = load_inputs(json_path, limit=5)  # Using fewer inputs for testing

    # Define test scenarios - same as LiteLLM pattern
    test_scenarios = [
        {
            "name": "1_conscious_false_no_auto",
            "conscious_ingest": False,
            "auto_ingest": None,
            "description": "conscious_ingest=False (no auto_ingest specified)",
        },
        {
            "name": "2_conscious_true_no_auto",
            "conscious_ingest": True,
            "auto_ingest": None,
            "description": "conscious_ingest=True (no auto_ingest specified)",
        },
        {
            "name": "3_auto_true_only",
            "conscious_ingest": None,
            "auto_ingest": True,
            "description": "auto_ingest=True only",
        },
        {
            "name": "4_auto_false_only",
            "conscious_ingest": None,
            "auto_ingest": False,
            "description": "auto_ingest=False only",
        },
        {
            "name": "5_both_false",
            "conscious_ingest": False,
            "auto_ingest": False,
            "description": "Both conscious_ingest and auto_ingest = False",
        },
        {
            "name": "6_both_true",
            "conscious_ingest": True,
            "auto_ingest": True,
            "description": "Both conscious_ingest and auto_ingest = True",
        },
    ]

    # Clean up previous test databases
    if os.path.exists("test_databases_azure_openai"):
        print("Cleaning up previous Azure OpenAI test databases...")
        shutil.rmtree("test_databases_azure_openai")

    print("🔷 Starting Azure OpenAI Test Suite")
    print(
        f"Testing {len(test_scenarios)} configurations with {len(test_inputs)} inputs each"
    )
    print(f"Azure Endpoint: {azure_config['endpoint']}")
    print(f"Deployment: {azure_config['deployment']}\n")

    successful_tests = 0

    # Run each test scenario
    for scenario in test_scenarios:
        # Handle None values by only passing specified parameters
        kwargs = {}
        if scenario["conscious_ingest"] is not None:
            kwargs["conscious_ingest"] = scenario["conscious_ingest"]
        if scenario["auto_ingest"] is not None:
            kwargs["auto_ingest"] = scenario["auto_ingest"]

        success = run_azure_test_scenario(
            test_name=scenario["name"],
            conscious_ingest=kwargs.get("conscious_ingest", False),
            auto_ingest=kwargs.get("auto_ingest", False),
            test_inputs=test_inputs,
            azure_config=azure_config,
        )

        if success:
            successful_tests += 1

        # Pause between tests
        print("Pausing for 3 seconds before next test...")
        time.sleep(3)

    print("\n" + "=" * 60)
    print(
        f"✅ Azure OpenAI tests completed! ({successful_tests}/{len(test_scenarios)} successful)"
    )
    print("=" * 60)
    print(
        "\nAzure OpenAI test databases created in 'test_databases_azure_openai/' directory:"
    )
    for scenario in test_scenarios:
        db_path = f"test_databases_azure_openai/{scenario['name']}/memory.db"
        if os.path.exists(db_path):
            size = os.path.getsize(db_path) / 1024  # Size in KB
            print(f"  - {scenario['name']}: {size:.2f} KB")

    return successful_tests > 0


if __name__ == "__main__":
    main()
