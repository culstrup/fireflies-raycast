#!/usr/bin/env python3

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fireflies_api import FirefliesAPI


def search_april_meetings():
    """Search for April meetings to see why they weren't found."""

    api = FirefliesAPI()

    print("🔍 Searching for April 2025 meetings...\n")

    query = """
    query MyTranscripts($limit: Int, $skip: Int) {
      transcripts(limit: $limit, skip: $skip, mine: true) {
        id
        title
        dateString
        date
        host_email
        organizer_email
        participants
        meeting_attendees {
          email
        }
      }
    }
    """

    skip = 0
    april_meetings = []
    all_agentgrid_meetings = []

    # Search through more meetings
    while skip < 200:
        try:
            data = api.execute_query(query, {"limit": 20, "skip": skip})

            if not data or "transcripts" not in data:
                break

            batch = data["transcripts"]
            if not batch:
                break

            for transcript in batch:
                date_str = transcript.get("dateString", "")
                title = transcript.get("title", "")

                # Check if it's an April 2025 meeting
                if "2025-04" in date_str:
                    april_meetings.append({"date": date_str, "title": title})

                    # Check for agentgrid participants
                    all_emails = []

                    # Collect all emails
                    if transcript.get("host_email"):
                        all_emails.append(transcript["host_email"])
                    if transcript.get("organizer_email"):
                        all_emails.append(transcript["organizer_email"])

                    participants = transcript.get("participants", []) or []
                    for p in participants:
                        if p and "," in str(p):
                            all_emails.extend([e.strip() for e in p.split(",") if "@" in e])
                        elif p and "@" in str(p):
                            all_emails.append(p)

                    attendees = transcript.get("meeting_attendees", []) or []
                    for a in attendees:
                        if a and a.get("email"):
                            all_emails.append(a["email"])

                    # Check if any agentgrid email
                    has_agentgrid = any("@agentgrid.net" in str(e).lower() for e in all_emails)

                    if has_agentgrid:
                        all_agentgrid_meetings.append(
                            {
                                "date": date_str,
                                "title": title,
                                "emails": [e for e in all_emails if "@agentgrid.net" in str(e).lower()],
                            }
                        )
                        print(f"✅ Found AgentGrid meeting: {title}")
                        print(f"   Date: {date_str}")
                        print(f"   AgentGrid emails: {[e for e in all_emails if '@agentgrid.net' in str(e).lower()]}")
                        print()

            skip += 20

            # Show progress
            if batch:
                oldest = batch[-1].get("dateString", "Unknown")
                print(f"Checked {skip} meetings (oldest: {oldest})...")

                # Stop if we've gone past March
                if "2025-03" in oldest:
                    print("Reached March 2025, stopping search...")
                    break

            if len(batch) < 20:
                break

        except Exception as e:
            print(f"Error: {e}")
            break

    print("\n📊 Summary:")
    print(f"Found {len(april_meetings)} total April 2025 meetings")
    print(f"Found {len(all_agentgrid_meetings)} AgentGrid meetings in April")

    if april_meetings:
        print("\n📅 All April 2025 meetings:")
        for m in sorted(april_meetings, key=lambda x: x["date"]):
            print(f"  {m['date']} - {m['title']}")


if __name__ == "__main__":
    search_april_meetings()
