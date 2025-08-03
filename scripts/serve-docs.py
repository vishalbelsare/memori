#!/usr/bin/env python3
"""
Development script to serve MkDocs documentation locally
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Serve documentation locally"""
    project_root = Path(__file__).parent.parent
    
    print("🚀 Starting Memoriai documentation server...")
    print("📚 Documentation will be available at: http://127.0.0.1:8000")
    print("🔄 Auto-reload enabled - changes will update automatically")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Check if mkdocs is installed
        subprocess.run(["mkdocs", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ MkDocs not found. Installing documentation dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", project_root / "docs" / "requirements.txt"
        ], check=True)
    
    # Serve documentation
    try:
        subprocess.run([
            "mkdocs", "serve", 
            "--config-file", project_root / "mkdocs.yml"
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Documentation server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error serving documentation: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())