#!/usr/bin/env python3
"""
Wrapper script to run the comprehensive OpenAI Provider Test Suite from the root directory.

This script provides convenient access to the complete OpenAI provider testing suite,
which includes tests for:
- Standard OpenAI API
- Azure OpenAI
- Ollama (local OpenAI-compatible server)

Each provider is tested with all combinations of conscious_ingest and auto_ingest parameters
to validate memory behavior across different configurations.

Usage:
    python openai_test_suite.py

Or make it executable:
    chmod +x openai_test_suite.py
    ./openai_test_suite.py

Environment Variables:
    # Standard OpenAI
    OPENAI_API_KEY=sk-your-api-key-here
    OPENAI_MODEL=gpt-4o  # optional, defaults to gpt-4o

    # Azure OpenAI
    AZURE_OPENAI_API_KEY=your-azure-api-key
    AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
    AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
    AZURE_OPENAI_API_VERSION=2024-02-15-preview  # optional

    # Ollama (local)
    OLLAMA_BASE_URL=http://localhost:11434/v1  # optional
    OLLAMA_MODEL=llama3.1  # optional
"""

import os
import subprocess
import sys


def main():
    # Get the actual test suite path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_suite_path = os.path.join(
        script_dir, "tests", "openai_support", "openai_test_suite.py"
    )

    # Check for virtual environment Python first
    venv_python = os.path.join(script_dir, ".venv", "bin", "python")

    if os.path.exists(venv_python):
        python_cmd = venv_python
        print(f"🐍 Using virtual environment Python: {venv_python}")
    else:
        python_cmd = sys.executable
        print(f"🐍 Using system Python: {python_cmd}")

    # Display information about the test suite
    print("\n🤖 MEMORI OPENAI PROVIDER TEST SUITE")
    print("=" * 50)
    print("This comprehensive test suite validates Memori's compatibility")
    print("with multiple OpenAI-compatible providers:")
    print("• Standard OpenAI API")
    print("• Azure OpenAI")
    print("• Ollama (local)")
    print()
    print("Each provider tests all combinations of conscious_ingest/auto_ingest")
    print("parameters to ensure proper memory behavior.")
    print("=" * 50)

    # Check if test suite exists
    if os.path.exists(test_suite_path):
        print(f"📁 Test suite found at: {test_suite_path}")
        print("🚀 Starting comprehensive OpenAI provider tests...\n")

        # Run the actual test suite
        result = subprocess.run([python_cmd, test_suite_path] + sys.argv[1:])

        # Exit with same code as test suite
        sys.exit(result.returncode)
    else:
        print(f"❌ Error: Test suite not found at {test_suite_path}")
        print("\nExpected file structure:")
        print("  memori/")
        print("  ├── openai_test_suite.py  (this wrapper)")
        print("  └── tests/")
        print("      └── openai_support/")
        print("          ├── openai_test_suite.py  (main test suite)")
        print("          ├── openai_test.py")
        print("          ├── azure_openai_test.py")
        print("          └── ollama_test.py")
        print("\nPlease ensure the test files are in the correct location.")
        sys.exit(1)


if __name__ == "__main__":
    main()
