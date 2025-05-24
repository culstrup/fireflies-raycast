#!/usr/bin/env python3

import os
import sys

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fireflies_api import FirefliesAPI


def test_domain_search(domain: str, limit: int = 50):
    """Test if we can find meetings with participants from a specific domain."""

    api = FirefliesAPI()
    found_meetings = []

    print(f"🔍 Testing domain search for: {domain}\n")

    # Query with participant email fields
    query = """
    query MyTranscripts($limit: Int, $skip: Int) {
      transcripts(limit: $limit, skip: $skip, mine: true) {
        id
        title
        dateString
        host_email
        organizer_email
        participants
        fireflies_users
        meeting_attendees {
          email
          name
        }
      }
    }
    """

    skip = 0
    total_checked = 0

    while total_checked < limit:
        try:
            data = api.execute_query(query, {"limit": 10, "skip": skip})

            if not data or "transcripts" not in data:
                break

            batch = data["transcripts"]
            if not batch:
                break

            for transcript in batch:
                # Collect all emails from various fields
                all_emails = []

                # Add host email
                if transcript.get("host_email"):
                    all_emails.append(transcript["host_email"])

                # Add organizer email
                if transcript.get("organizer_email"):
                    all_emails.append(transcript["organizer_email"])

                # Add participants
                participants = transcript.get("participants", []) or []
                for p in participants:
                    if p and "," in p:
                        all_emails.extend([e.strip() for e in p.split(",") if "@" in e])
                    elif p and "@" in p:
                        all_emails.append(p)

                # Add fireflies users
                ff_users = transcript.get("fireflies_users", []) or []
                all_emails.extend([u for u in ff_users if u and "@" in u])

                # Add meeting attendees
                attendees = transcript.get("meeting_attendees", []) or []
                for a in attendees:
                    if a and a.get("email"):
                        all_emails.append(a["email"])

                # Check if any email matches the domain
                domain_found = any(email.lower().endswith(f"@{domain.lower()}") for email in all_emails)

                if domain_found:
                    found_meetings.append(transcript)
                    matching_emails = [e for e in all_emails if e.lower().endswith(f"@{domain.lower()}")]
                    print(f"✅ Found: {transcript['title']}")
                    print(f"   Date: {transcript['dateString']}")
                    print(f"   Matching emails: {matching_emails}")
                    print()

            skip += 10
            total_checked += len(batch)

            # Show progress
            if batch:
                print(f"Checked {total_checked} meetings (oldest: {batch[-1]['dateString']})...")

            if len(batch) < 10:
                break

        except Exception as e:
            print(f"Error: {e}")
            break

    print(f"\n📊 Summary: Checked {total_checked} meetings, found {len(found_meetings)} with @{domain} participants")

    return found_meetings


if __name__ == "__main__":
    if len(sys.argv) > 1:
        domain = sys.argv[1]
    else:
        domain = "fpt.org.pl"

    test_domain_search(domain)
