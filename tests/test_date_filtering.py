#!/usr/bin/env python3

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generate_case_study_from_domain import DomainCaseStudyGenerator


class TestDateFiltering(unittest.TestCase):
    """Test date filtering functionality in case study generator."""

    @patch("generate_case_study_from_domain.genai")
    @patch("generate_case_study_from_domain.FirefliesAPI")
    @patch.dict(os.environ, {"GOOGLE_AI_STUDIO_KEY": "test-key"})
    def setUp(self, mock_fireflies_api, mock_genai):
        """Set up test fixtures."""
        self.mock_api = MagicMock()
        mock_fireflies_api.return_value = self.mock_api
        self.generator = DomainCaseStudyGenerator("example.com", days_back=10)

    def test_date_filtering_includes_recent_meetings(self):
        """Test that recent meetings within date range are included."""
        recent_date = datetime.now() - timedelta(days=5)

        mock_transcripts = [
            {
                "title": "Recent Meeting",
                "dateString": recent_date.isoformat() + "Z",
                "participants": ["user@example.com"],
            }
        ]

        self.mock_api.execute_query.return_value = {"transcripts": mock_transcripts}

        meetings = self.generator.fetch_domain_meetings()

        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0]["title"], "Recent Meeting")

    def test_date_filtering_excludes_old_meetings(self):
        """Test that old meetings outside date range are excluded."""
        old_date = datetime.now() - timedelta(days=15)
        recent_date = datetime.now() - timedelta(days=5)

        mock_transcripts = [
            {
                "title": "Recent Meeting",
                "dateString": recent_date.isoformat() + "Z",
                "participants": ["user@example.com"],
            },
            {
                "title": "Old Meeting",
                "dateString": old_date.isoformat() + "Z",
                "participants": ["user@example.com"],
            },
        ]

        # First call returns both meetings
        self.mock_api.execute_query.return_value = {"transcripts": mock_transcripts}

        meetings = self.generator.fetch_domain_meetings()

        # Should only include recent meeting
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0]["title"], "Recent Meeting")

    def test_stops_fetching_when_old_date_reached(self):
        """Test that fetching stops when meetings older than date range are found."""
        old_date = datetime.now() - timedelta(days=15)

        # First batch has old meeting
        first_batch = [
            {
                "title": "Old Meeting",
                "dateString": old_date.isoformat() + "Z",
                "participants": ["user@example.com"],
            }
        ]

        self.mock_api.execute_query.return_value = {"transcripts": first_batch}

        meetings = self.generator.fetch_domain_meetings()

        # Should have called API only once (stopped after hitting old date)
        self.assertEqual(self.mock_api.execute_query.call_count, 1)
        self.assertEqual(len(meetings), 0)  # No meetings within date range

    def test_timezone_handling(self):
        """Test that timezone differences are handled correctly."""
        # Create date with timezone info
        date_with_tz = datetime.now().replace(tzinfo=None) - timedelta(days=5)

        mock_transcripts = [
            {
                "title": "Meeting with TZ",
                "dateString": date_with_tz.isoformat() + "Z",
                "participants": ["user@example.com"],
            }
        ]

        self.mock_api.execute_query.return_value = {"transcripts": mock_transcripts}

        # Should not raise timezone comparison error
        meetings = self.generator.fetch_domain_meetings()
        self.assertEqual(len(meetings), 1)

    def test_parse_date_fallbacks(self):
        """Test date parsing with various formats and fallbacks."""
        # Test with dateString
        transcript1 = {"dateString": "2025-01-15T10:00:00Z"}
        date1 = self.generator._parse_date(transcript1)
        self.assertIsInstance(date1, datetime)

        # Test with timestamp
        timestamp = int(datetime.now().timestamp() * 1000)
        transcript2 = {"date": timestamp}
        date2 = self.generator._parse_date(transcript2)
        self.assertIsInstance(date2, datetime)

        # Test with no date (should default to now)
        transcript3 = {}
        date3 = self.generator._parse_date(transcript3)
        self.assertIsInstance(date3, datetime)
        # Should be close to current time
        self.assertLess((datetime.now() - date3).seconds, 2)

    def test_date_filtering_with_mixed_formats(self):
        """Test date filtering with mixed date formats."""
        recent_date = datetime.now() - timedelta(days=5)
        old_date = datetime.now() - timedelta(days=15)

        mock_transcripts = [
            {
                "title": "Recent with dateString",
                "dateString": recent_date.isoformat() + "Z",
                "participants": ["user@example.com"],
            },
            {
                "title": "Recent with timestamp",
                "date": int(recent_date.timestamp() * 1000),
                "participants": ["user@example.com"],
            },
            {
                "title": "Old with dateString",
                "dateString": old_date.isoformat() + "Z",
                "participants": ["user@example.com"],
            },
        ]

        self.mock_api.execute_query.return_value = {"transcripts": mock_transcripts}

        meetings = self.generator.fetch_domain_meetings()

        # Should include both recent meetings
        self.assertEqual(len(meetings), 2)
        titles = [m["title"] for m in meetings]
        self.assertIn("Recent with dateString", titles)
        self.assertIn("Recent with timestamp", titles)
        self.assertNotIn("Old with dateString", titles)


if __name__ == "__main__":
    unittest.main()
