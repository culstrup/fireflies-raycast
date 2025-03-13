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
    
    @patch('requests.post')
    def test_format_transcript(self, mock_post):
        """Test transcript formatting"""
        
        # Import the module
        from fetch_fireflies_from_chrome_tabs import format_transcript
        
        # Create a mock transcript
        transcript = {
            "title": "Test Meeting",
            "dateString": "2025-01-01T12:00:00Z",
            "summary": {
                "overview": "This is a test summary"
            },
            "sentences": [
                {
                    "speaker_name": "Alice",
                    "text": "Hello, this is a test."
                },
                {
                    "speaker_name": "Bob",
                    "text": "Testing, 1, 2, 3."
                }
            ]
        }
        
        formatted = format_transcript(transcript)
        
        # Check that key elements are in the formatted text
        self.assertIn("Test Meeting", formatted)
        self.assertIn("2025-01-01T12:00:00Z", formatted)
        self.assertIn("This is a test summary", formatted)
        self.assertIn("Alice: Hello, this is a test.", formatted)
        self.assertIn("Bob: Testing, 1, 2, 3.", formatted)
        
        # Test with missing summary
        transcript_no_summary = {
            "title": "Test Meeting",
            "dateString": "2025-01-01T12:00:00Z",
            "sentences": [
                {
                    "speaker_name": "Alice",
                    "text": "Hello, this is a test."
                }
            ]
        }
        
        formatted_no_summary = format_transcript(transcript_no_summary)
        
        # Verify it still works without a summary
        self.assertIn("Test Meeting", formatted_no_summary)
        self.assertIn("Alice: Hello, this is a test.", formatted_no_summary)
        self.assertNotIn("Summary", formatted_no_summary)

if __name__ == '__main__':
    unittest.main()