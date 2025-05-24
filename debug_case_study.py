#!/usr/bin/env python3

import os
import re
import sys
from datetime import datetime, timedelta

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from fireflies_api import FirefliesAPI


def debug_domain_search(domain, days_back=90):
    """Debug version to see what's happening with domain search."""

    print(f"🔍 DEBUG: Searching for domain '{domain}' in last {days_back} days")

    # Configure API
    api = FirefliesAPI()

    # Calculate date range
    from_date = datetime.now() - timedelta(days=days_back)
    from_date_str = from_date.strftime("%Y-%m-%d")

    print(f"📅 Date filter: {from_date_str} to today")

    # Fetch first batch only for debugging (without date filter to see older meetings)
    query = """
    query MyTranscripts($limit: Int) {
      transcripts(limit: $limit, mine: true) {
        id
        title
        dateString
        date
        organizer_email
        summary {
          overview
        }
        sentences {
          text
          raw_text
          speaker_name
        }
      }
    }
    """

    variables = {"limit": 30}

    print("🚀 Fetching sample meetings...")
    data = api.execute_query(query, variables)

    if not data or "transcripts" not in data:
        print("❌ No data returned from API")
        return

    transcripts = data["transcripts"]
    print(f"📊 Found {len(transcripts)} recent meetings")

    for i, transcript in enumerate(transcripts):
        print(f"\n--- Meeting {i+1} ---")
        print(f"Title: {transcript.get('title', 'N/A')}")
        print(f"Date: {transcript.get('dateString', 'N/A')}")
        print(f"Organizer: {transcript.get('organizer_email', 'N/A')}")

        # Debug email extraction
        emails = extract_participant_emails_debug(transcript)
        print(f"Extracted emails: {emails}")

        # Check domain match
        domain_match = any(email.endswith(f"@{domain}") for email in emails)
        print(f"Domain match for '{domain}': {domain_match}")

        if domain_match:
            print("✅ FOUND DOMAIN MATCH!")
        else:
            print("❌ No domain match")


def extract_participant_emails_debug(transcript):
    """Debug version of email extraction with detailed output."""
    emails = []

    print("  🔍 Email extraction debug:")

    # Check organizer email
    organizer_email = transcript.get("organizer_email", "") or ""
    if organizer_email and "@" in organizer_email:
        emails.append(organizer_email.lower())
        print(f"    Organizer: {organizer_email}")

    # Check title
    title = transcript.get("title", "") or ""
    if title:
        title_emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", title)
        if title_emails:
            emails.extend([e.lower() for e in title_emails])
            print(f"    From title: {title_emails}")

    # Check sentences (first 10 only for debug)
    sentences = transcript.get("sentences", []) or []
    speaker_emails = []
    unique_speakers = set()

    for sentence in sentences[:10]:  # Check first 10 for debug
        if not sentence:
            continue
        speaker = sentence.get("speaker_name", "") or ""
        if speaker:
            unique_speakers.add(speaker)
            sentence_emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", speaker)
            speaker_emails.extend(sentence_emails)

    print(f"    Unique speakers found: {list(unique_speakers)}")

    if speaker_emails:
        emails.extend([e.lower() for e in speaker_emails])
        print(f"    From speakers: {speaker_emails}")

    # Deduplicate
    unique_emails = list(set(emails))
    print(f"    Total unique: {unique_emails}")

    return unique_emails


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_case_study.py <domain> [days_back]")
        sys.exit(1)

    domain = sys.argv[1]
    days_back = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    debug_domain_search(domain, days_back)
