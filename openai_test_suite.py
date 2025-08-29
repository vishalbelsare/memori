#!/usr/bin/env python3
"""
Wrapper script to run the OpenAI test suite from the root directory.
"""

import sys
import os
import subprocess

def main():
    # Get the actual test suite path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_suite_path = os.path.join(script_dir, "tests", "openai", "openai_support", "openai_test_suite.py")
    
    # Check for virtual environment Python first
    venv_python = os.path.join(script_dir, ".venv", "bin", "python")
    
    if os.path.exists(venv_python):
        python_cmd = venv_python
    else:
        python_cmd = sys.executable
    
    # Run the actual test suite
    if os.path.exists(test_suite_path):
        result = subprocess.run([python_cmd, test_suite_path] + sys.argv[1:])
        sys.exit(result.returncode)
    else:
        print(f"Error: OpenAI test suite not found at {test_suite_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()