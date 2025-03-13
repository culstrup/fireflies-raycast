#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
import importlib

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules that are imported in the code
sys.modules['pyperclip'] = MagicMock()
sys.modules['subprocess'] = MagicMock()

class TestFirefliesClipboard(unittest.TestCase):
    
    def setUp(self):
        # Ensure we have a fresh import for each test
        if 'fireflies_clipboard' in sys.modules:
            del sys.modules['fireflies_clipboard']
    
    @patch('sys.exit')
    @patch('requests.post')
    @patch('dotenv.load_dotenv', return_value=True)
    def test_no_api_key(self, mock_dotenv, mock_post, mock_exit):
        """Test behavior when no API key is set"""
        
        # Mock every call to os.environ.get to return empty string
        with patch('os.environ.get', return_value=""):
            # Now import the module with mocked env
            import fireflies_clipboard
            # Run the main function
            fireflies_clipboard.main()
            
            # Assert that sys.exit was called with error code 1
            mock_exit.assert_called_once_with(1)
            # Assert that requests.post was not called
            mock_post.assert_not_called()
    
    @patch('requests.post')
    @patch('dotenv.load_dotenv', return_value=True)
    def test_api_call_made(self, mock_dotenv, mock_post):
        """Test that API call is made with the correct parameters"""
        
        # Create a response mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "transcripts": []  # Empty list to simulate no transcripts
            }
        }
        mock_post.return_value = mock_response
        
        # Mock environment to return fake API key
        with patch('os.environ.get', return_value="fake-api-key"):
            # Import the module with mocked env
            import fireflies_clipboard
            
            # Run the main function with sys.exit patched to prevent actual exit
            with patch('sys.exit'):
                fireflies_clipboard.main()
            
            # Assert that requests.post was called
            mock_post.assert_called_once()
            
            # Get the arguments it was called with
            args, kwargs = mock_post.call_args
            
            # Assert that the API endpoint is correct
            self.assertEqual(args[0], "https://api.fireflies.ai/graphql")
            
            # Assert that the Authorization header contains the API key
            self.assertEqual(kwargs['headers']['Authorization'], "Bearer fake-api-key")
            
            # Assert that the request contains a GraphQL query
            self.assertIn("query", kwargs['json'])

if __name__ == '__main__':
    unittest.main()