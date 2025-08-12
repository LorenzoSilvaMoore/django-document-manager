#!/usr/bin/env python
"""
Simple script to build and test the package locally
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and print status"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"{'='*50}")
    
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        return False
    else:
        print(f"✅ Success: {description}")
        return True

def main():
    """Main build and test process"""
    commands = [
        ("python -m pip install -e .", "Installing package in development mode"),
        ("python -m pytest tests/", "Running tests"),
        ("python setup.py sdist bdist_wheel", "Building distribution packages"),
        ("twine check dist/*", "Checking built packages"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            sys.exit(1)
    
    print(f"\n{'='*50}")
    print("🎉 All steps completed successfully!")
    print("Your package is ready for distribution.")
    print("To upload to PyPI, run: twine upload dist/*")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
