#!/usr/bin/env python3

import os
import sys
import unittest
from unittest.mock import patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generate_case_study_from_domain import DomainCaseStudyGenerator


class TestDomainCaseStudyGenerator(unittest.TestCase):
    """Test cases for the DomainCaseStudyGenerator class."""

    @patch("generate_case_study_from_domain.genai")
    @patch("generate_case_study_from_domain.FirefliesAPI")
    @patch.dict(os.environ, {"GOOGLE_AI_STUDIO_KEY": "test-key"})
    def test_init(self, mock_fireflies_api, mock_genai):
        """Test initialization of the generator."""
        generator = DomainCaseStudyGenerator("example.com", days_back=90)

        self.assertEqual(generator.domain, "example.com")
        self.assertEqual(generator.days_back, 90)
        mock_genai.configure.assert_called_once_with(api_key="test-key")

    @patch("generate_case_study_from_domain.genai")
    @patch("generate_case_study_from_domain.FirefliesAPI")
    def test_init_no_api_key(self, mock_fireflies_api, mock_genai):
        """Test initialization fails without API key."""
        with self.assertRaises(ValueError) as context:
            DomainCaseStudyGenerator("example.com")

        self.assertIn("GOOGLE_AI_STUDIO_KEY", str(context.exception))

    @patch("generate_case_study_from_domain.genai")
    @patch("generate_case_study_from_domain.FirefliesAPI")
    @patch.dict(os.environ, {"GOOGLE_AI_STUDIO_KEY": "test-key"})
    def test_extract_participant_emails(self, mock_fireflies_api, mock_genai):
        """Test extraction of participant emails from transcript."""
        generator = DomainCaseStudyGenerator("example.com")

        transcript = {
            "title": "Meeting with john@example.com",
            "participants": ["john@example.com", "jane@other.com, bob@example.com"],
            "host_email": "host@example.com",
            "meeting_attendees": [
                {"email": "attendee@example.com", "name": "Attendee"},
            ],
            "sentences": [
                {"speaker_name": "John", "text": "Hello"},
                {"speaker_name": "Jane", "text": "Hi"},
                {"speaker_name": "Bob", "text": "Welcome"},
            ],
        }

        emails = generator.extract_participant_emails(transcript)

        self.assertIn("john@example.com", emails)
        self.assertIn("jane@other.com", emails)
        self.assertIn("bob@example.com", emails)
        self.assertIn("host@example.com", emails)
        self.assertIn("attendee@example.com", emails)
        self.assertEqual(len(emails), 5)

    @patch("generate_case_study_from_domain.genai")
    @patch("generate_case_study_from_domain.FirefliesAPI")
    @patch.dict(os.environ, {"GOOGLE_AI_STUDIO_KEY": "test-key"})
    def test_is_domain_participant(self, mock_fireflies_api, mock_genai):
        """Test checking if transcript has domain participants."""
        generator = DomainCaseStudyGenerator("example.com")

        # Transcript with domain participant
        transcript_with = {
            "participants": ["john@example.com", "other@company.com"],
            "sentences": [{"speaker_name": "John", "text": "Hello"}],
        }
        self.assertTrue(generator.is_domain_participant(transcript_with))

        # Transcript without domain participant
        transcript_without = {
            "participants": ["jane@other.com", "bob@another.com"],
            "sentences": [{"speaker_name": "Jane", "text": "Hello"}],
        }
        self.assertFalse(generator.is_domain_participant(transcript_without))

    @patch("generate_case_study_from_domain.genai")
    @patch("generate_case_study_from_domain.FirefliesAPI")
    @patch.dict(os.environ, {"GOOGLE_AI_STUDIO_KEY": "test-key"})
    def test_prepare_for_gemini(self, mock_fireflies_api, mock_genai):
        """Test preparing transcripts for Gemini."""
        generator = DomainCaseStudyGenerator("example.com")

        transcripts = [
            {
                "title": "Test Meeting",
                "dateString": "January 15, 2025",
                "transcript_url": "https://example.com/transcript",
                "summary": {"overview": "Test summary"},
                "sentences": [{"speaker_name": "John", "text": "Hello everyone"}],
            }
        ]

        content, metadata = generator.prepare_for_gemini(transcripts)

        self.assertIn("Test Meeting", content)
        self.assertIn("January 15, 2025", content)
        self.assertIn("Test summary", content)
        self.assertIn("John: Hello everyone", content)

        self.assertEqual(metadata["domain"], "example.com")
        self.assertEqual(metadata["meeting_count"], 1)
        self.assertFalse(metadata["truncated"])

    @patch("generate_case_study_from_domain.genai")
    @patch("generate_case_study_from_domain.FirefliesAPI")
    @patch.dict(os.environ, {"GOOGLE_AI_STUDIO_KEY": "test-key"})
    def test_empty_domain(self, mock_fireflies_api, mock_genai):
        """Test that empty domain raises error."""
        with self.assertRaises(ValueError) as context:
            DomainCaseStudyGenerator("")

        self.assertIn("Domain cannot be empty", str(context.exception))


if __name__ == "__main__":
    unittest.main()
