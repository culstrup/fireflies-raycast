#!/usr/bin/env python3
"""Tests for timestamp functionality in Fireflies API"""

import unittest

from fireflies_api import FirefliesAPI


class TestTimestamps(unittest.TestCase):
    """Test timestamp functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.api = FirefliesAPI("test_api_key")

    def test_format_transcript_with_timestamps(self):
        """Test that timestamps are correctly formatted in transcripts"""
        # Mock transcript with timestamps
        transcript = {
            "title": "Test Meeting",
            "dateString": "2025-06-05T10:00:00.000Z",
            "summary": {"overview": "Test summary"},
            "sentences": [
                {"speaker_name": "Alice", "text": "Hello everyone", "start_time": 0.5, "end_time": 2.3},
                {"speaker_name": "Bob", "text": "Hi Alice", "start_time": 3.0, "end_time": 4.5},
                {
                    "speaker_name": "Alice",
                    "text": "Let's start the meeting",
                    "start_time": 65.5,  # Over 1 minute
                    "end_time": 68.0,
                },
            ],
        }

        # Format the transcript
        formatted = self.api.format_transcript(transcript)

        # Check that timestamps are included
        self.assertIn("[00:00] Alice: Hello everyone", formatted)
        self.assertIn("[00:03] Bob: Hi Alice", formatted)
        self.assertIn("[01:05] Alice: Let's start the meeting", formatted)

    def test_format_transcript_without_timestamps(self):
        """Test backward compatibility when timestamps are not available"""
        # Mock transcript without timestamps
        transcript = {
            "title": "Test Meeting",
            "dateString": "2025-06-05T10:00:00.000Z",
            "summary": {"overview": "Test summary"},
            "sentences": [
                {"speaker_name": "Alice", "text": "Hello everyone"},
                {"speaker_name": "Bob", "text": "Hi Alice"},
            ],
        }

        # Format the transcript
        formatted = self.api.format_transcript(transcript)

        # Check that it falls back to the old format without timestamps
        self.assertIn("Alice: Hello everyone", formatted)
        self.assertIn("Bob: Hi Alice", formatted)
        self.assertNotIn("[", formatted)  # No timestamps

    def test_format_transcript_mixed_timestamps(self):
        """Test handling of mixed sentences with and without timestamps"""
        # Mock transcript with some sentences having timestamps
        transcript = {
            "title": "Test Meeting",
            "dateString": "2025-06-05T10:00:00.000Z",
            "summary": None,
            "sentences": [
                {"speaker_name": "Alice", "text": "Hello", "start_time": 0.0},
                {
                    "speaker_name": "Bob",
                    "text": "Hi",
                    # No timestamp
                },
                {"speaker_name": "Charlie", "text": "Hey", "start_time": 5.5},
            ],
        }

        # Format the transcript
        formatted = self.api.format_transcript(transcript)

        # Check mixed formatting
        self.assertIn("[00:00] Alice: Hello", formatted)
        self.assertIn("Bob: Hi", formatted)  # No timestamp
        self.assertNotIn("[", formatted.split("Bob: Hi")[0].split("\n")[-1])  # Bob's line has no timestamp
        self.assertIn("[00:05] Charlie: Hey", formatted)

    def test_timestamp_formatting_edge_cases(self):
        """Test edge cases in timestamp formatting"""
        # Test with various timestamp values
        transcript = {
            "title": "Test Meeting",
            "dateString": "2025-06-05T10:00:00.000Z",
            "sentences": [
                {
                    "speaker_name": "Alice",
                    "text": "Exactly one hour",
                    "start_time": 3600.0,  # Exactly 1 hour
                },
                {
                    "speaker_name": "Bob",
                    "text": "Over an hour",
                    "start_time": 3661.5,  # 1 hour, 1 minute, 1.5 seconds
                },
                {"speaker_name": "Charlie", "text": "Almost a minute", "start_time": 59.9},
            ],
        }

        # Format the transcript
        formatted = self.api.format_transcript(transcript)

        # Check formatting of edge cases
        self.assertIn("[60:00] Alice: Exactly one hour", formatted)
        self.assertIn("[61:01] Bob: Over an hour", formatted)
        self.assertIn("[00:59] Charlie: Almost a minute", formatted)


if __name__ == "__main__":
    unittest.main()
