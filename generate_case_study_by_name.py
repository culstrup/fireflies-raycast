#!/usr/bin/env python3

import os
import sys

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fireflies_api import FirefliesAPI


def find_meetings_by_participant_name(participant_name: str, limit: int = 10):
    """Find meetings where a specific person participated."""

    api = FirefliesAPI()
    matching_meetings = []

    print(f"🔍 Searching for meetings with participant: {participant_name}")

    # Fetch recent meetings
    query = """
    query MyTranscripts($limit: Int, $skip: Int) {
      transcripts(limit: $limit, skip: $skip, mine: true) {
        id
        title
        dateString
        transcript_url
        sentences {
          speaker_name
        }
      }
    }
    """

    skip = 0
    total_searched = 0

    while total_searched < 500:  # Search up to 500 meetings
        try:
            data = api.execute_query(query, {"limit": limit, "skip": skip})

            if not data or "transcripts" not in data:
                break

            batch = data["transcripts"]
            if not batch:
                break

            # Check each transcript for the participant
            for transcript in batch:
                # Get unique speakers
                speakers = set()
                sentences = transcript.get("sentences", [])
                if sentences:  # Check if sentences is not None
                    for sentence in sentences:
                        if sentence and sentence.get("speaker_name"):
                            speakers.add(sentence["speaker_name"])

                # Check if our participant is in this meeting
                for speaker in speakers:
                    if participant_name.lower() in speaker.lower():
                        matching_meetings.append(
                            {
                                "id": transcript["id"],
                                "title": transcript["title"],
                                "date": transcript["dateString"],
                                "url": transcript["transcript_url"],
                                "matched_speaker": speaker,
                            }
                        )
                        print(f"✅ Found: {transcript['title']} ({transcript['dateString']})")
                        break

            skip += limit
            total_searched += len(batch)

            # Show progress
            if batch:
                oldest_date = batch[-1].get("dateString", "Unknown")
                print(f"  Searched {total_searched} meetings so far (oldest: {oldest_date})...")

            if len(batch) < limit:
                break

        except Exception as e:
            print(f"Error: {e}")
            break

    print(f"\n📊 Searched {total_searched} meetings, found {len(matching_meetings)} with {participant_name}")
    return matching_meetings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_case_study_by_name.py <participant_name>")
        print("Example: python generate_case_study_by_name.py 'Lukasz Owczarek'")
        sys.exit(1)

    participant_name = sys.argv[1]
    meetings = find_meetings_by_participant_name(participant_name)

    print("\n📋 Summary of meetings found:")
    for meeting in meetings:
        print(f"\n- {meeting['title']}")
        print(f"  Date: {meeting['date']}")
        print(f"  Speaker: {meeting['matched_speaker']}")
        print(f"  URL: {meeting['url']}")
