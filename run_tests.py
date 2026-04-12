#!/usr/bin/env python3
"""
Quick test runner with summary statistics.
Usage: python run_tests.py [options]
"""

import subprocess
import sys
from pathlib import Path


def run_tests(verbose=False, coverage=False, specific=None):
    """Run pytest with various options."""
    
    cmd = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing"])
    
    if specific:
        cmd.append(specific)
    
    print(f"Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if "--coverage" in sys.argv:
            exit_code = run_tests(verbose=True, coverage=True)
        elif "--verbose" in sys.argv or "-v" in sys.argv:
            exit_code = run_tests(verbose=True)
        elif "--help" in sys.argv or "-h" in sys.argv:
            print(__doc__)
            exit_code = 0
        else:
            exit_code = run_tests(verbose=True)
    else:
        # Default: run all tests with summary
        exit_code = run_tests(verbose=True)
    
    sys.exit(exit_code)
