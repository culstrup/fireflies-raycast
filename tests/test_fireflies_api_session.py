#!/usr/bin/env python3

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestFirefliesAPISession(unittest.TestCase):
    @patch("requests.Session")
    @patch("fireflies_api.load_dotenv")
    def test_api_session_creation(self, mock_load_dotenv, mock_session_class):
        """Test that the API creates and uses a requests Session"""

        # Import the module
        from fireflies_api import FirefliesAPI

        # Mock environment variables
        with patch.dict(os.environ, {"FIREFLIES_API_KEY": "test-api-key"}):
            # Create API instance
            _ = FirefliesAPI()  # Creating instance to test session setup

            # Verify Session was created
            mock_session_class.assert_called_once()

            # Verify session headers were set correctly
            session = mock_session_class.return_value
            session.headers.update.assert_called_once()
            headers_call = session.headers.update.call_args[0][0]
            self.assertEqual(headers_call["Content-Type"], "application/json")
            self.assertEqual(headers_call["Authorization"], "Bearer test-api-key")

    @patch("requests.Session")
    @patch("fireflies_api.load_dotenv")
    def test_api_uses_session_for_requests(self, mock_load_dotenv, mock_session_class):
        """Test that the API uses the session for requests"""

        # Import the module
        from fireflies_api import FirefliesAPI

        # Create mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_session.post.return_value = mock_response

        # Mock environment variables
        with patch.dict(os.environ, {"FIREFLIES_API_KEY": "test-api-key"}):
            # Create API instance
            api = FirefliesAPI()

            # Call execute_query
            _ = api.execute_query("test query", {"var": "value"})  # Testing the call, not the result

            # Verify session's post method was called correctly
            mock_session.post.assert_called_once()

            # Check arguments
            args, kwargs = mock_session.post.call_args
            self.assertEqual(args[0], "https://api.fireflies.ai/graphql")
            self.assertEqual(kwargs["json"]["query"], "test query")
            self.assertEqual(kwargs["json"]["variables"], {"var": "value"})
            self.assertEqual(kwargs["timeout"], (5, 60))  # Default timeout tuple (connect, read)

    @patch("requests.Session")
    @patch("fireflies_api.load_dotenv")
    def test_api_session_timeout(self, mock_load_dotenv, mock_session_class):
        """Test that the API respects custom timeouts"""

        # Import the module
        from fireflies_api import FirefliesAPI

        # Create mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_session.post.return_value = mock_response

        # Mock environment variables
        with patch.dict(os.environ, {"FIREFLIES_API_KEY": "test-api-key"}):
            # Create API instance
            api = FirefliesAPI()

            # Call execute_query with custom timeout
            custom_timeout = 30
            _ = api.execute_query("test query", {"var": "value"}, timeout=custom_timeout)  # Testing timeout param

            # Verify timeout was passed correctly
            kwargs = mock_session.post.call_args[1]
            self.assertEqual(kwargs["timeout"], (5, custom_timeout))  # Timeout tuple (connect, read)


if __name__ == "__main__":
    unittest.main()
