#!/usr/bin/env python3

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock modules that are imported in the code
sys.modules["pyperclip"] = MagicMock()
sys.modules["subprocess"] = MagicMock()


class TestFirefliesClipboard(unittest.TestCase):
    def setUp(self):
        # Ensure we have a fresh import for each test
        if "fireflies_clipboard" in sys.modules:
            del sys.modules["fireflies_clipboard"]
        if "fireflies_api" in sys.modules:
            del sys.modules["fireflies_api"]

    @patch("sys.exit")
    @patch("fireflies_api.FirefliesAPI")
    def test_no_api_key(self, mock_api_class, mock_exit):
        """Test behavior when no API key is set"""

        # Make FirefliesAPI raise ValueError when initialized
        mock_api_class.side_effect = ValueError("FIREFLIES_API_KEY not set")

        # Now import the module
        import fireflies_clipboard

        # Run the main function
        fireflies_clipboard.main()

        # Assert that sys.exit was called with error code 1
        # We expect it could be called multiple times due to nested exception handling
        # So we just check that it was called at least once with the right code
        self.assertTrue(mock_exit.call_count >= 1)
        mock_exit.assert_any_call(1)

    @patch("fireflies_api.FirefliesAPI")
    def test_api_integration(self, mock_api_class):
        """Test integration with FirefliesAPI class"""

        # Create a mock FirefliesAPI instance
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        # Mock get_recent_transcripts to return a list with one transcript
        transcript = {
            "title": "Test Meeting",
            "dateString": "2025-01-01T12:00:00Z",
            "summary": {"overview": "Test summary"},
            "sentences": [{"speaker_name": "Alice", "text": "Hello"}],
        }
        mock_api.get_recent_transcripts.return_value = [transcript]

        # Mock format_transcript to return a simple string
        mock_api.format_transcript.return_value = "Formatted transcript"

        # Import the module
        import fireflies_clipboard

        # Patch setup_clipboard to check what gets processed
        with patch("fireflies_clipboard.setup_clipboard") as mock_clipboard:
            # Patch date_parser.isoparse to avoid actually parsing the date
            with patch("dateutil.parser.isoparse", return_value="2025-01-01"):
                # Run the main function
                fireflies_clipboard.main()

        # Verify API was initialized
        mock_api_class.assert_called_once()

        # Verify get_recent_transcripts was called
        mock_api.get_recent_transcripts.assert_called_once()

        # Verify format_transcript was called with the transcript
        mock_api.format_transcript.assert_called_once_with(transcript)

        # Verify clipboard was set up with the formatted transcript
        mock_clipboard.assert_called_once_with("Formatted transcript")

    @patch("fireflies_api.FirefliesAPI")
    def test_processing_transcript(self, mock_api_class):
        """Test handling of a transcript that's still processing"""

        # Create a mock FirefliesAPI instance
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        # Mock get_recent_transcripts to return a transcript without sentences
        processing_transcript = {
            "title": "Processing Meeting",
            "dateString": "2025-01-01T12:00:00Z",
            "summary": {"overview": "Test summary"},
            "sentences": [],  # Empty sentences indicates processing
        }
        mock_api.get_recent_transcripts.return_value = [processing_transcript]

        # Import the module
        import fireflies_clipboard

        # Run the main function with patched print and exit
        with patch("builtins.print") as mock_print:
            with patch("sys.exit"):
                fireflies_clipboard.main()

        # Verify a message about processing was printed
        mock_print.assert_any_call(
            "The latest meeting 'Processing Meeting' is still processing. Transcript not available yet."
        )  # noqa: E501

        # Verify format_transcript was NOT called
        mock_api.format_transcript.assert_not_called()


if __name__ == "__main__":
    unittest.main()
