#!/usr/bin/env python3

import os
import sys

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fireflies_api import FirefliesAPI
from generate_case_study_from_domain import DomainCaseStudyGenerator


def test_fpt_meetings():
    """Test if we can find FPT domain in known meetings."""

    # Known meeting IDs with FPT participants
    meeting_ids = [
        "01JTVT3CCTWFQVRMFKVZ824X1M",  # StartSmart CEE workshop
        "01JTVT3CCYQHQ4SGW7VCGXRCZA",  # Case Selection for AI Workshop
    ]

    api = FirefliesAPI()
    generator = DomainCaseStudyGenerator("fpt.org.pl", days_back=30)

    print("🔍 Testing FPT domain detection in known meetings...\n")

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
                    text
                }
            }
        }
        """

        print(f"\n{'='*60}")
        print(f"Fetching meeting ID: {meeting_id}")

        try:
            data = api.execute_query(query, {"transcriptId": meeting_id})
            if data and "transcript" in data:
                transcript = data["transcript"]
                print(f"✅ Title: {transcript.get('title', 'N/A')}")
                print(f"📅 Date: {transcript.get('dateString', 'N/A')}")
                print(f"📧 Organizer: {transcript.get('organizer_email', 'N/A')}")

                # Extract participant emails
                emails = generator.extract_participant_emails(transcript)
                print(f"\n🔍 Extracted emails: {emails}")

                # Check for FPT domain
                fpt_emails = [e for e in emails if e.endswith("@fpt.org.pl")]
                if fpt_emails:
                    print(f"✅ FPT emails found: {fpt_emails}")
                else:
                    print("❌ No FPT emails found")

                # Show speaker names to debug
                print("\n👥 Speaker names (first 10):")
                speakers = set()
                sentences = transcript.get("sentences", [])[:20]
                for s in sentences:
                    if s and s.get("speaker_name"):
                        speakers.add(s["speaker_name"])

                for speaker in list(speakers)[:10]:
                    print(f"   - {speaker}")

                # Look for mentions of FPT or the known email in text
                print("\n📝 Searching for FPT mentions in transcript text...")
                fpt_mentions = 0
                for s in sentences[:50]:  # Check first 50 sentences
                    if s and s.get("text"):
                        text = s["text"].lower()
                        if "fpt" in text or "owczarek" in text:
                            print(f"   Found mention: {s['text'][:100]}...")
                            fpt_mentions += 1

                if fpt_mentions == 0:
                    print("   No FPT mentions found in first 50 sentences")

            else:
                print("❌ Could not fetch transcript")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_fpt_meetings()
