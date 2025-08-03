"""
Test runner script for Memoriai.

This script provides convenient ways to run different types of tests
with appropriate configurations.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> int:
    """Run a command and return the exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Memoriai Test Runner")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "performance", "all"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        default=False,
        help="Run with coverage reporting",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--parallel",
        "-n",
        type=int,
        help="Number of parallel workers",
    )
    parser.add_argument(
        "--markers",
        help="Additional pytest markers (e.g., 'not slow')",
    )
    parser.add_argument(
        "--file",
        help="Specific test file to run",
    )

    args = parser.parse_args()

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test type filter
    if args.type == "unit":
        cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
    elif args.type == "performance":
        cmd.extend(["-m", "performance"])

    # Add coverage if requested (and pytest-cov is available)
    if args.coverage and args.type != "performance":
        try:
            import subprocess
            result = subprocess.run([sys.executable, "-c", "import pytest_cov"], capture_output=True)
            if result.returncode == 0:
                cmd.extend(
                    [
                        "--cov=memoriai",
                        "--cov-report=html:htmlcov",
                        "--cov-report=term-missing",
                        "--cov-report=xml",
                    ]
                )
            else:
                print("Warning: pytest-cov not installed, running tests without coverage")
        except Exception:
            print("Warning: pytest-cov not available, running tests without coverage")

    # Add fast filter
    if args.fast:
        marker = "not slow"
        if args.markers:
            args.markers = f"{args.markers} and {marker}"
        else:
            args.markers = marker

    # Add custom markers
    if args.markers:
        cmd.extend(["-m", args.markers])

    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.extend(["--tb=short"])

    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Add specific file
    if args.file:
        cmd.append(args.file)
    else:
        cmd.append("tests/")

    # Run the tests
    exit_code = run_command(cmd, f"Running {args.type} tests")

    if exit_code == 0:
        print(f"\n✅ {args.type.title()} tests passed!")

        if args.coverage and args.type != "performance":
            print("\n📊 Coverage report generated:")
            print("  - HTML: htmlcov/index.html")
            print("  - XML: coverage.xml")
    else:
        print(f"\n❌ {args.type.title()} tests failed!")

    return exit_code


def run_quality_checks():
    """Run code quality checks."""
    checks = [
        (
            ["python", "-m", "black", "--check", "memoriai/", "tests/"],
            "Black formatting",
        ),
        (["python", "-m", "ruff", "check", "memoriai/", "tests/"], "Ruff linting"),
        (["python", "-m", "mypy", "memoriai/"], "MyPy type checking"),
        (["python", "-m", "bandit", "-r", "memoriai/"], "Bandit security check"),
        (["python", "-m", "safety", "check"], "Safety dependency check"),
    ]

    failed_checks = []

    for cmd, description in checks:
        exit_code = run_command(cmd, description)
        if exit_code != 0:
            failed_checks.append(description)

    if failed_checks:
        print(f"\n❌ Failed quality checks: {', '.join(failed_checks)}")
        return 1
    else:
        print("\n✅ All quality checks passed!")
        return 0


def run_full_ci():
    """Run the full CI pipeline locally."""
    print("🚀 Running full CI pipeline...")

    # Run quality checks
    quality_exit = run_quality_checks()
    if quality_exit != 0:
        return quality_exit

    # Run unit tests
    unit_exit = run_command(
        ["python", "-m", "pytest", "-m", "unit", "--cov=memoriai"],
        "Unit tests with coverage",
    )
    if unit_exit != 0:
        return unit_exit

    # Run integration tests
    integration_exit = run_command(
        ["python", "-m", "pytest", "-m", "integration"], "Integration tests"
    )
    if integration_exit != 0:
        return integration_exit

    print("\n🎉 Full CI pipeline completed successfully!")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quality":
        exit_code = run_quality_checks()
    elif len(sys.argv) > 1 and sys.argv[1] == "ci":
        exit_code = run_full_ci()
    else:
        exit_code = main()

    sys.exit(exit_code)
