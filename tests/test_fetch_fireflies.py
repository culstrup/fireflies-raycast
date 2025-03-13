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

class TestFetchFireflies(unittest.TestCase):
    
    @patch('fetch_fireflies_from_chrome_tabs.get_chrome_tabs')
    def test_extract_transcript_ids(self, mock_get_tabs):
        """Test extraction of transcript IDs from URLs"""
        
        # Import the module
        from fetch_fireflies_from_chrome_tabs import extract_transcript_ids
        
        # Test with valid Fireflies URLs
        urls = [
            "https://fireflies.ai/view/meeting-123::ABC123",
            "https://fireflies.ai/view/another-meeting::XYZ789",
            "https://fireflies.ai/view/third-one::DEF456"
        ]
        
        expected_ids = ["ABC123", "XYZ789", "DEF456"]
        actual_ids = extract_transcript_ids(urls)
        
        self.assertEqual(actual_ids, expected_ids)
        
        # Test with invalid URLs
        invalid_urls = [
            "https://fireflies.ai/dashboard",
            "https://example.com",
            "https://fireflies.ai/view/invalid"
        ]
        
        self.assertEqual(extract_transcript_ids(invalid_urls), [])
    
    @patch('fireflies_api.FirefliesAPI')
    def test_api_integration(self, mock_api_class):
        """Test integration with FirefliesAPI class"""
        
        # Import the module
        import fetch_fireflies_from_chrome_tabs
        
        # Create a mock FirefliesAPI instance
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        
        # Mock the get_transcript_by_id method
        transcript = {
            "title": "Test Meeting",
            "dateString": "2025-01-01T12:00:00Z",
            "summary": {"overview": "Test summary"},
            "sentences": [
                {"speaker_name": "Alice", "text": "Hello"}
            ]
        }
        mock_api.get_transcript_by_id.return_value = transcript
        
        # Mock format_transcript to return a simple string
        mock_api.format_transcript.return_value = "Formatted transcript"
        
        # Patch the functions that would normally find transcripts
        with patch('fetch_fireflies_from_chrome_tabs.get_chrome_tabs', return_value=["url1"]):
            with patch('fetch_fireflies_from_chrome_tabs.extract_transcript_ids', return_value=["id1"]):
                # Patch pyperclip.copy to check what gets copied
                with patch('pyperclip.copy') as mock_copy:
                    # Run the main function with sys.exit and print patched
                    with patch('sys.exit'):
                        with patch('builtins.print'):
                            fetch_fireflies_from_chrome_tabs.main()
                    
                    # Verify API was initialized
                    mock_api_class.assert_called_once()
                    
                    # Verify get_transcript_by_id was called
                    mock_api.get_transcript_by_id.assert_called_with("id1")
                    
                    # Verify format_transcript was called
                    mock_api.format_transcript.assert_called_with(transcript)
                    
                    # Verify something was copied to clipboard (with newlines added)
                    mock_copy.assert_called_once()
                    args = mock_copy.call_args[0][0]
                    self.assertIn("Formatted transcript", args)

if __name__ == '__main__':
    unittest.main()