#!/usr/bin/env python3
"""
Run all example projects to test OmniBuilder.

This script runs each example and verifies the outputs.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_example(example_dir: Path) -> dict:
    """Run a single example and return results."""
    print(f"\n{'='*60}")
    print(f"Running example: {example_dir.name}")
    print(f"{'='*60}")

    result = {
        "name": example_dir.name,
        "success": False,
        "message": "",
        "duration": 0
    }

    readme_path = example_dir / "README.md"
    if not readme_path.exists():
        result["message"] = "No README.md found"
        return result

    # Extract goal from README
    with open(readme_path) as f:
        content = f.read()

    # Look for omnibuilder command
    goal = None
    for line in content.split("\n"):
        if "omnibuilder run" in line:
            # Extract the goal from quotes
            start = line.find('"') + 1
            end = line.rfind('"')
            if start > 0 and end > start:
                goal = line[start:end]
                break

    if not goal:
        result["message"] = "No omnibuilder command found in README"
        return result

    print(f"Goal: {goal}")
    print(f"Working directory: {example_dir}")

    # Run omnibuilder
    start_time = datetime.now()

    try:
        process = subprocess.run(
            ["omnibuilder", "run", goal],
            cwd=example_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        duration = (datetime.now() - start_time).total_seconds()
        result["duration"] = duration

        if process.returncode == 0:
            result["success"] = True
            result["message"] = "Completed successfully"
            print(f"✓ Success ({duration:.1f}s)")
        else:
            result["message"] = f"Failed with code {process.returncode}"
            print(f"✗ Failed: {result['message']}")
            if process.stderr:
                print(f"Error: {process.stderr[:500]}")

    except subprocess.TimeoutExpired:
        result["message"] = "Timeout after 5 minutes"
        print(f"✗ {result['message']}")
    except Exception as e:
        result["message"] = str(e)
        print(f"✗ Exception: {e}")

    return result


def main():
    """Run all examples and generate report."""
    print("OmniBuilder Example Test Suite")
    print(f"Started: {datetime.now()}")

    examples_dir = Path(__file__).parent
    results = []

    # Find all example directories
    example_dirs = [
        d for d in examples_dir.iterdir()
        if d.is_dir() and not d.name.startswith(('.', '__'))
    ]

    if not example_dirs:
        print("No example directories found!")
        return 1

    print(f"\nFound {len(example_dirs)} examples")

    # Run each example
    for example_dir in sorted(example_dirs):
        result = run_example(example_dir)
        results.append(result)

    # Generate summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful

    print(f"\nTotal examples: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if results:
        avg_duration = sum(r["duration"] for r in results) / len(results)
        print(f"Average duration: {avg_duration:.1f}s")

    print("\nDetailed Results:")
    for result in results:
        status = "✓" if result["success"] else "✗"
        print(f"{status} {result['name']}: {result['message']} ({result['duration']:.1f}s)")

    # Save report
    report_path = examples_dir / "test_report.txt"
    with open(report_path, "w") as f:
        f.write(f"OmniBuilder Example Test Report\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        f.write(f"Total: {total}, Successful: {successful}, Failed: {failed}\n\n")
        for result in results:
            f.write(f"{result['name']}: {result['message']} ({result['duration']:.1f}s)\n")

    print(f"\nReport saved to: {report_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
