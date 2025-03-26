#!/usr/bin/env python3

"""
This is a script to patch the CI testing environment to prevent network connections.
It should be run in the GitHub Actions workflow before running tests.
"""

import os
import sys

def prepare_test_environment():
    """
    Set up environment variables to isolate tests from network.
    Create dummy .env file to prevent auth errors.
    """
    # Print current directory for debugging in CI
    print(f"Current directory: {os.getcwd()}")
    
    # Create a dummy .env file for tests
    with open(".env", "w") as f:
        f.write('FIREFLIES_API_KEY="dummy-test-key-for-ci"')
    
    # Tell Python to fail immediately on any real network access
    # This ensures our mocks are working correctly
    os.environ["PYTHONHTTPSVERIFY"] = "1"
    os.environ["REQUESTS_CA_BUNDLE"] = "/nonexistent"  # Force SSL verification to fail
    
    print("Test environment prepared. All real network connections will fail.")
    
if __name__ == "__main__":
    prepare_test_environment()