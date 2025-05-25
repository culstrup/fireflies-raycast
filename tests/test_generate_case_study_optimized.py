#!/usr/bin/env python3

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generate_case_study_optimized import OptimizedCaseStudyGenerator


class TestOptimizedCaseStudyGenerator(unittest.TestCase):
    """Test cases for the OptimizedCaseStudyGenerator class."""

    @patch("generate_case_study_optimized.genai")
    @patch("generate_case_study_optimized.FirefliesAPI")
    @patch.dict(os.environ, {"GOOGLE_AI_STUDIO_KEY": "test-key"})
    def setUp(self, mock_fireflies_api, mock_genai):
        """Set up test fixtures."""
        self.mock_api = MagicMock()
        mock_fireflies_api.return_value = self.mock_api
        self.generator = OptimizedCaseStudyGenerator("example.com", days_back=30)

    def test_extract_participant_emails(self):
        """Test extraction of participant emails."""
        transcript = {
            "participants": ["user@example.com", "other@test.com"],
            "host_email": "host@example.com",
            "meeting_attendees": [{"email": "attendee@example.com"}],
        }

        emails = self.generator.extract_participant_emails(transcript)

        self.assertIn("user@example.com", emails)
        self.assertIn("other@test.com", emails)
        self.assertIn("host@example.com", emails)
        self.assertIn("attendee@example.com", emails)

    def test_is_domain_participant(self):
        """Test domain participant checking."""
        # With domain participant
        transcript_with = {"participants": ["user@example.com"]}
        self.assertTrue(self.generator.is_domain_participant(transcript_with))

        # Without domain participant
        transcript_without = {"participants": ["user@other.com"]}
        self.assertFalse(self.generator.is_domain_participant(transcript_without))

    def test_fetch_domain_meetings(self):
        """Test fetching domain meetings with date filtering."""
        # Mock API responses for pagination
        recent_date = datetime.now() - timedelta(days=5)
        old_date = datetime.now() - timedelta(days=60)

        # First call returns mixed meetings
        first_batch = [
            {
                "id": "1",
                "title": "Recent Meeting",
                "dateString": recent_date.isoformat() + "Z",
                "participants": ["user@example.com"],
            },
            {
                "id": "2",
                "title": "Old Meeting",
                "dateString": old_date.isoformat() + "Z",
                "participants": ["user@example.com"],
            },
        ]

        # Second call returns empty (end of results)
        self.mock_api.execute_query.side_effect = [
            {"transcripts": first_batch},
            {"transcripts": []},
        ]

        meetings = self.generator.fetch_domain_meetings()

        # The optimized version includes all domain meetings it finds
        # It stops early but doesn't filter by date
        self.assertEqual(len(meetings), 2)
        # They are sorted by date (oldest first for chronological order)
        self.assertEqual(meetings[0]["title"], "Old Meeting")
        self.assertEqual(meetings[1]["title"], "Recent Meeting")

    def test_prepare_for_gemini(self):
        """Test preparing content for Gemini."""
        transcripts = [
            {
                "title": "Test Meeting",
                "dateString": "2025-01-15T10:00:00Z",
                "transcript_url": "https://example.com/1",
                "participants": ["user@example.com"],
                "summary": {"overview": "Test summary"},
                "sentences": [
                    {
                        "speaker_name": "John",
                        "text": "This is a long sentence that should be included in the excerpts.",
                    },
                    {"speaker_name": "Jane", "text": "Short"},
                ],
            }
        ]

        content = self.generator.prepare_for_gemini(transcripts)

        self.assertIn("Test Meeting", content)
        self.assertIn("user@example.com", content)
        self.assertIn("Test summary", content)
        self.assertIn("This is a long sentence", content)
        self.assertNotIn("Short", content)  # Too short for excerpts

    @patch("generate_case_study_optimized.subprocess.run")
    def test_generate_with_clipboard(self, mock_subprocess):
        """Test generate method with clipboard output."""
        # Mock successful flow
        self.mock_api.execute_query.return_value = {
            "transcripts": [
                {
                    "title": "Meeting",
                    "dateString": datetime.now().isoformat() + "Z",
                    "participants": ["user@example.com"],
                    "sentences": [],
                }
            ]
        }

        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = "Generated case study content"
        self.generator.model.generate_content.return_value = mock_response

        # Run generate
        self.generator.generate()

        # Check subprocess was called to copy to clipboard
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        self.assertEqual(call_args[0][0], ["pbcopy"])
        self.assertIn(b"Generated case study content", call_args[1]["input"])

    def test_generate_no_meetings(self):
        """Test generate when no meetings found."""
        self.mock_api.execute_query.return_value = {"transcripts": []}

        result = self.generator.generate()

        self.assertIsNone(result)

    def test_handle_none_summary(self):
        """Test handling of None summary field."""
        transcripts = [
            {
                "title": "Test Meeting",
                "dateString": "2025-01-15T10:00:00Z",
                "summary": None,  # None instead of dict
                "sentences": [],
            }
        ]

        # Should not raise exception
        content = self.generator.prepare_for_gemini(transcripts)
        self.assertIn("Test Meeting", content)

    def test_handle_empty_sentences(self):
        """Test handling of empty sentences."""
        transcripts = [
            {
                "title": "Test Meeting",
                "dateString": "2025-01-15T10:00:00Z",
                "sentences": None,  # None instead of list
            }
        ]

        # Should not raise exception
        content = self.generator.prepare_for_gemini(transcripts)
        self.assertIn("Test Meeting", content)


if __name__ == "__main__":
    unittest.main()
