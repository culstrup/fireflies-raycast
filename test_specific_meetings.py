#!/usr/bin/env python3

import logging
import os
import sys

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fireflies_api import FirefliesAPI

logger = logging.getLogger(__name__)


def test_specific_meetings():
    """Test fetching specific meetings by ID and check different query approaches."""

    # Meeting IDs from the URLs
    meeting_ids = [
        "01JTVT3CCTWFQVRMFKVZ824X1M",  # StartSmart CEE workshop
        "01JTVT3CCYQHQ4SGW7VCGXRCZA",  # Case Selection for AI Workshop
    ]

    api = FirefliesAPI()

    print("🔍 Testing different query approaches to find the FPT meetings...\n")

    # Test 1: Try to fetch specific transcript by ID
    print("Test 1: Fetching specific transcripts by ID")
    for meeting_id in meeting_ids:
        query = """
        query GetTranscript($transcriptId: String!) {
            transcript(id: $transcriptId) {
                id
                title
                dateString
                organizer_email
                sentences {
                    speaker_name
                }
            }
        }
        """

        try:
            data = api.execute_query(query, {"transcriptId": meeting_id})
            if data and "transcript" in data:
                transcript = data["transcript"]
                print(f"✅ Found: {transcript.get('title', 'N/A')}")
                print(f"   Date: {transcript.get('dateString', 'N/A')}")
                print(f"   Organizer: {transcript.get('organizer_email', 'N/A')}")
                speakers = set()
                for s in transcript.get("sentences", []):
                    if s and s.get("speaker_name"):
                        speakers.add(s["speaker_name"])
                print(f"   Speakers: {list(speakers)[:5]}")
            else:
                print(f"❌ Could not fetch transcript {meeting_id}")
        except Exception as e:
            print(f"❌ Error fetching {meeting_id}: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test 2: Query without mine:true filter
    print("Test 2: Fetching transcripts WITHOUT 'mine: true' filter")
    query = """
    query MyTranscripts($limit: Int) {
      transcripts(limit: $limit) {
        id
        title
        dateString
        organizer_email
      }
    }
    """

    try:
        data = api.execute_query(query, {"limit": 20})
        if data and "transcripts" in data:
            transcripts = data["transcripts"]
            print(f"📊 Found {len(transcripts)} transcripts without 'mine' filter")

            # Show date range
            if transcripts:
                dates = [t.get("dateString", "N/A") for t in transcripts]
                print(f"   Date range: {dates[-1]} to {dates[0]}")

            # Check if our target meetings are in this list
            for t in transcripts:
                if any(mid in t.get("id", "") for mid in meeting_ids):
                    print(f"✅ FOUND TARGET MEETING: {t.get('title')}")
                # Also check for workshop/StartSmart in titles
                title = t.get("title", "").lower()
                if "workshop" in title or "startsmart" in title:
                    print(f"🎯 Workshop found: {t.get('title')} - {t.get('dateString')}")
        else:
            print("❌ No data returned")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test 3: Try with user_id parameter
    print("Test 3: Fetching with user_id parameter")
    query = """
    query MyTranscripts($limit: Int) {
      transcripts(limit: $limit, user_id: "me") {
        id
        title
        dateString
        organizer_email
      }
    }
    """

    try:
        data = api.execute_query(query, {"limit": 20})
        if data and "transcripts" in data:
            transcripts = data["transcripts"]
            print(f"📊 Found {len(transcripts)} transcripts with user_id='me'")

            # List the first few titles
            for i, t in enumerate(transcripts[:5]):
                print(f"   {i+1}. {t.get('title', 'N/A')} - {t.get('dateString', 'N/A')}")
        else:
            print("❌ No data returned")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test 4: Check if meetings are shared/accessible differently
    print("Test 4: Searching for meetings with 'workshop' or 'StartSmart' in title")
    query = """
    query SearchTranscripts($search: String!) {
      transcripts(search: $search, limit: 20) {
        id
        title
        dateString
        organizer_email
      }
    }
    """

    for search_term in ["workshop", "StartSmart", "CEE", "polish"]:
        try:
            data = api.execute_query(query, {"search": search_term})
            if data and "transcripts" in data:
                transcripts = data["transcripts"]
                if transcripts:
                    print(f"🔍 Search '{search_term}' found {len(transcripts)} results:")
                    for t in transcripts[:3]:
                        print(f"   - {t.get('title', 'N/A')}")
        except Exception as e:
            # Search parameter might not be supported
            logger.debug(f"Search for '{search_term}' failed: {e}")


if __name__ == "__main__":
    test_specific_meetings()
