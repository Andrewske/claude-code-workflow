#!/usr/bin/env python3
"""
Project health check script.

Runs common diagnostic checks and reports status.

Usage:
    ./check_health.py [--verbose]
"""

import subprocess
import sys
import argparse
from typing import Tuple, List


def run_check(name: str, command: str, verbose: bool = False) -> Tuple[bool, str]:
    """Run a single health check."""
    if verbose:
        print(f"\n{'='*50}")
        print(f"Running: {name}")
        print(f"Command: {command}")
        print('='*50)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() or result.stdout.strip()
            
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Project health check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    # Define checks - customize for your project
    checks: List[Tuple[str, str]] = [
        ("TypeScript compilation", "npx tsc --noEmit"),
        ("ESLint", "npm run lint -- --quiet"),
        # ("Database connection", "npm run db:check"),
        # ("Redis connection", "redis-cli ping"),
        # ("External API", "curl -s https://api.example.com/health"),
    ]
    
    results = []
    
    print("Running health checks...\n")
    
    for name, command in checks:
        passed, output = run_check(name, command, args.verbose)
        results.append((name, passed, output))
        
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
        
        if not passed and not args.verbose:
            print(f"   Error: {output[:100]}...")
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    
    print(f"Passed: {passed_count}/{total_count}")
    
    if passed_count < total_count:
        print("\nFailed checks:")
        for name, passed, output in results:
            if not passed:
                print(f"  - {name}")
        sys.exit(1)
    else:
        print("\nAll checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
