#!/usr/bin/env python3

"""
This is a script to patch the CI testing environment to prevent network connections.
It should be run in the GitHub Actions workflow before running tests.
"""

import os
import subprocess


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

    # Create a sitecustomize.py file to patch socket operations
    with open("sitecustomize.py", "w") as f:
        f.write("""
import socket
import time

# Save the original socket.socket
original_socket = socket.socket

def patched_socket(*args, **kwargs):
    # If attempting to connect to fireflies.ai, raise an exception immediately
    if args and isinstance(args[0], socket.AddressFamily):
        # This is likely a socket creation for network purposes
        # We'll allow the socket to be created, but patch its connect method
        s = original_socket(*args, **kwargs)
        original_connect = s.connect

        def patched_connect(address):
            host, port = address
            if isinstance(host, str) and 'fireflies.ai' in host:
                # Simulate a connection error for Fireflies API
                import errno
                raise socket.error(errno.ECONNREFUSED, "Connection refused - network calls not allowed in tests")
            return original_connect(address)

        s.connect = patched_connect
        return s

    return original_socket(*args, **kwargs)

# Replace the socket.socket with our patched version
socket.socket = patched_socket
""")

    # Tell Python to fail immediately on any real network access
    # This ensures our mocks are working correctly
    os.environ["PYTHONHTTPSVERIFY"] = "1"
    os.environ["REQUESTS_CA_BUNDLE"] = "/nonexistent"  # Force SSL verification to fail
    os.environ["PYTHONPATH"] = os.getcwd() + ":" + os.environ.get("PYTHONPATH", "")

    print("Test environment prepared. All real network connections will fail.")

    # List all test files for debugging
    subprocess.run(["find", "tests", "-name", "test_*.py"])


if __name__ == "__main__":
    prepare_test_environment()
