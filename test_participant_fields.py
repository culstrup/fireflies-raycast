#!/usr/bin/env python3

import os
import sys

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fireflies_api import FirefliesAPI


def test_participant_fields():
    """Test the participant email fields in Fireflies API."""

    # Known meeting with FPT participant
    meeting_id = "01JTVT3CCTWFQVRMFKVZ824X1M"  # StartSmart CEE workshop

    api = FirefliesAPI()

    print("🔍 Testing participant email fields...\n")

    query = """
    query GetTranscript($transcriptId: String!) {
        transcript(id: $transcriptId) {
            id
            title
            dateString

            # Email fields
            host_email
            organizer_email

            # Participant arrays
            participants
            fireflies_users

            # Detailed attendee info
            meeting_attendees {
                displayName
                email
                phoneNumber
                name
                location
            }

            # Sample speaker names for comparison
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

            print(f"📋 Meeting: {transcript['title']}\n")

            print("📧 Email Fields:")
            print(f"   Host Email: {transcript.get('host_email', 'N/A')}")
            print(f"   Organizer Email: {transcript.get('organizer_email', 'N/A')}")

            print("\n👥 Participants (email array):")
            participants = transcript.get("participants", [])
            if participants:
                for email in participants:
                    print(f"   - {email}")
                    if email and "@fpt.org.pl" in email:
                        print("     ✅ FPT DOMAIN FOUND!")
            else:
                print("   None found")

            print("\n🔥 Fireflies Users:")
            ff_users = transcript.get("fireflies_users", [])
            if ff_users:
                for email in ff_users:
                    print(f"   - {email}")
            else:
                print("   None found")

            print("\n📋 Meeting Attendees (detailed):")
            attendees = transcript.get("meeting_attendees", [])
            if attendees:
                for attendee in attendees:
                    print(f"   - Name: {attendee.get('name', 'N/A')}")
                    print(f"     Email: {attendee.get('email', 'N/A')}")
                    print(f"     Display Name: {attendee.get('displayName', 'N/A')}")
                    if attendee.get("email") and "@fpt.org.pl" in attendee.get("email", ""):
                        print("     ✅ FPT DOMAIN FOUND!")
            else:
                print("   None found")

        else:
            print("❌ Could not fetch transcript")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_participant_fields()
