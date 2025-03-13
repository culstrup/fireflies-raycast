#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules that are imported in the code
sys.modules['pyperclip'] = MagicMock()
sys.modules['subprocess'] = MagicMock()

class TestFirefliesClipboard(unittest.TestCase):
    
    @patch('requests.post')
    @patch('os.environ.get')
    def test_no_api_key(self, mock_env_get, mock_post):
        """Test behavior when no API key is set"""
        
        # Mock environment variable to return empty API key
        mock_env_get.return_value = ""
        
        # Import the module (which will use the mocked environment)
        from fireflies_clipboard import main
        
        # Run the main function with a patched sys.exit to prevent actual exit
        with patch('sys.exit') as mock_exit:
            main()
            # Assert that sys.exit was called with error code 1
            mock_exit.assert_called_once_with(1)
            
        # Assert that requests.post was not called
        mock_post.assert_not_called()
    
    @patch('requests.post')
    @patch('os.environ.get')
    def test_api_call_made(self, mock_env_get, mock_post):
        """Test that API call is made with the correct parameters"""
        
        # Mock environment variable to return a fake API key
        mock_env_get.return_value = "fake-api-key"
        
        # Create a response mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "transcripts": []  # Empty list to simulate no transcripts
            }
        }
        mock_post.return_value = mock_response
        
        # Import the module (which will use the mocked environment)
        from fireflies_clipboard import main
        
        # Run the main function
        main()
        
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