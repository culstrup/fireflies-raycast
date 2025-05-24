#!/usr/bin/env python3

import os
import sys

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fireflies_api import FirefliesAPI


def explore_transcript_fields():
    """Explore all available fields in a transcript to find where emails might be stored."""

    # Known meeting with FPT participant
    meeting_id = "01JTVT3CCTWFQVRMFKVZ824X1M"  # StartSmart CEE workshop

    api = FirefliesAPI()

    print("🔍 Exploring all available transcript fields...\n")

    # Query for fields we know exist
    query = """
    query GetTranscript($transcriptId: String!) {
        transcript(id: $transcriptId) {
            id
            title
            dateString
            organizer_email
            transcript_url

            # Try meeting_info as suggested
            meeting_info
            meeting_link

            # Summary fields
            summary {
                overview
            }

            # Sample sentences
            sentences(limit: 5) {
                speaker_name
                text
            }
        }
    }
    """

    try:
        data = api.execute_query(query, {"transcriptId": meeting_id})
        if data and "transcript" in data:
            transcript = data["transcript"]

            print(f"📋 Transcript: {transcript.get('title', 'N/A')}\n")

            # Check each field for email information
            print("🔍 Checking for email/participant information in all fields:\n")

            for field, value in transcript.items():
                if value is not None and value != "" and value != []:
                    print(f"📌 {field}:")
                    if isinstance(value, (list, dict)):
                        print(f"   {value}")
                    else:
                        print(f"   {str(value)[:200]}...")
                    print()

                    # Special check for email patterns in any string field
                    if isinstance(value, str) and "@" in value:
                        print("   ⚠️  Contains @ symbol!")
                        print()
        else:
            print("❌ Could not fetch transcript")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    explore_transcript_fields()
