#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import concurrent.futures
import time

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules that are imported in the code
sys.modules['pyperclip'] = MagicMock()
sys.modules['subprocess'] = MagicMock()

class TestParallelFetching(unittest.TestCase):
    
    def test_fetch_transcripts_parallel(self):
        """Test parallel transcript fetching"""
        
        # Import the module
        from fetch_fireflies_from_chrome_tabs import fetch_transcripts_parallel
        
        # Create mock API and transcript IDs
        mock_api = MagicMock()
        
        # Mock get_transcript_by_id to return different transcripts with different delays
        def mock_get_transcript(transcript_id, timeout=None):
            # Simulated response times to mimic real API behavior
            if transcript_id == "id1":
                response = {"id": "id1", "title": "Meeting 1"}
            elif transcript_id == "id2":
                response = {"id": "id2", "title": "Meeting 2"}
            elif transcript_id == "id3":
                response = {"id": "id3", "title": "Meeting 3"}
            else:
                return None
                
            return response
            
        mock_api.get_transcript_by_id.side_effect = mock_get_transcript
        
        transcript_ids = ["id1", "id2", "id3"]
        
        # Run the function
        result = fetch_transcripts_parallel(transcript_ids, mock_api)
        
        # Verify all transcripts were fetched
        self.assertEqual(len(result), 3)
        self.assertIn("id1", result)
        self.assertIn("id2", result)
        self.assertIn("id3", result)
        
        # Verify API called with correct parameters
        mock_api.get_transcript_by_id.assert_has_calls([
            call("id1", timeout=60),
            call("id2", timeout=60),
            call("id3", timeout=60)
        ], any_order=True)  # Order may vary due to parallel execution
    
    def test_fetch_transcripts_empty_list(self):
        """Test parallel fetching with empty list"""
        
        # Import the module
        from fetch_fireflies_from_chrome_tabs import fetch_transcripts_parallel
        
        # Create mock API
        mock_api = MagicMock()
        
        # Run with empty list
        result = fetch_transcripts_parallel([], mock_api)
        
        # Verify empty dictionary returned
        self.assertEqual(result, {})
        
        # Verify API not called
        mock_api.get_transcript_by_id.assert_not_called()
    
    def test_fetch_transcripts_with_errors(self):
        """Test parallel fetching handling errors"""
        
        # Import the module
        from fetch_fireflies_from_chrome_tabs import fetch_transcripts_parallel
        
        # Create mock API
        mock_api = MagicMock()
        
        # Make some transcripts fail
        def mock_get_transcript_with_errors(transcript_id, timeout=None):
            if transcript_id == "id1":
                return {"id": "id1", "title": "Success"}
            elif transcript_id == "id2":
                raise ValueError("API error")
            elif transcript_id == "id3":
                return None
            return None
            
        mock_api.get_transcript_by_id.side_effect = mock_get_transcript_with_errors
        
        transcript_ids = ["id1", "id2", "id3"]
        
        # Run the function
        result = fetch_transcripts_parallel(transcript_ids, mock_api)
        
        # Verify only successful transcripts are in result
        self.assertEqual(len(result), 1)
        self.assertIn("id1", result)
        self.assertNotIn("id2", result)  # Failed with exception
        self.assertNotIn("id3", result)  # Returned None
    
    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_worker_count(self, mock_executor_class):
        """Test worker count calculation"""
        
        # Import the module
        from fetch_fireflies_from_chrome_tabs import fetch_transcripts_parallel
        
        # Create mock executor and API
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        mock_api = MagicMock()
        
        # Test with different transcript counts
        scenarios = [
            (3, 3),    # 3 transcripts should use 3 workers
            (8, 8),    # 8 transcripts should use 8 workers
            (12, 10),  # 12 transcripts should max out at 10 workers
        ]
        
        for transcript_count, expected_workers in scenarios:
            transcript_ids = [f"id{i}" for i in range(transcript_count)]
            
            # Reset mock
            mock_executor_class.reset_mock()
            
            # Run with this number of transcripts
            fetch_transcripts_parallel(transcript_ids, mock_api)
            
            # Verify correct worker count
            mock_executor_class.assert_called_once_with(max_workers=expected_workers)
            
if __name__ == '__main__':
    unittest.main()