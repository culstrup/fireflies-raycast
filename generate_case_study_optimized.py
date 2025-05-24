#!/usr/bin/env python3
"""
Generate AI-powered case studies from Fireflies meetings filtered by participant domain.
Optimized version that stops searching after finding recent domain meetings.
"""

import os
import sys
import re
import logging
import subprocess
from typing import List, Dict
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fireflies_api import FirefliesAPI
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Case study generation prompt
CASE_STUDY_PROMPT = """You are a professional case study writer. Based on the following meeting transcripts with {domain} participants, create a compelling and professional case study.

Structure the case study as follows:

1. **Executive Summary** (2-3 sentences)
2. **Client Background** (Brief overview of the client)
3. **Challenge** (What problems were they facing?)
4. **Solution** (What approach and solutions were implemented?)
5. **Implementation Process** (Key steps and milestones)
6. **Results & Impact** (Concrete outcomes and benefits)
7. **Key Takeaways** (Lessons learned and best practices)

Use specific examples and quotes from the meetings where relevant. Keep the tone professional but engaging.

CLIENT DOMAIN: {domain}

MEETING TRANSCRIPTS:
{transcripts}
"""


class OptimizedCaseStudyGenerator:
    """Generate case studies from meetings filtered by participant domain."""
    
    def __init__(self, domain: str, days_back: int = 180):
        """Initialize the generator with optimized settings."""
        self.domain = domain.lower().strip()
        if not self.domain:
            raise ValueError("Domain cannot be empty")
            
        self.days_back = days_back
        self.fireflies_api = FirefliesAPI()
        
        # Configure Gemini
        api_key = os.getenv('GOOGLE_AI_STUDIO_KEY')
        if not api_key:
            raise ValueError("GOOGLE_AI_STUDIO_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.5 Pro Preview
        try:
            self.model = genai.GenerativeModel('gemini-2.5-pro-preview-05-06')
            logger.info("Initialized Gemini 2.5 Pro Preview model")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini 2.5 Pro: {e}")
            try:
                self.model = genai.GenerativeModel('gemini-1.5-pro')
                logger.info("Fell back to Gemini 1.5 Pro model")
            except:
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("Fell back to gemini-pro model")
    
    def extract_participant_emails(self, transcript: Dict) -> List[str]:
        """Extract all participant emails from a transcript using all available fields."""
        emails = []
        
        # Extract from participants array (primary source!)
        participants = transcript.get('participants', []) or []
        for participant in participants:
            if participant and isinstance(participant, str):
                # Handle comma-separated emails
                if ',' in participant:
                    emails.extend([e.strip() for e in participant.split(',') if '@' in e])
                elif '@' in participant:
                    emails.append(participant)
        
        # Extract from meeting_attendees
        attendees = transcript.get('meeting_attendees', []) or []
        for attendee in attendees:
            if attendee and attendee.get('email'):
                emails.append(attendee['email'])
        
        # Check host email
        host_email = transcript.get('host_email', '') or ''
        if host_email and '@' in host_email:
            emails.append(host_email)
        
        # Check organizer email
        organizer_email = transcript.get('organizer_email', '') or ''
        if organizer_email and '@' in organizer_email:
            emails.append(organizer_email)
        
        # Also check fireflies_users
        ff_users = transcript.get('fireflies_users', []) or []
        for user in ff_users:
            if user and '@' in user:
                emails.append(user)
        
        # Deduplicate and return
        return list(set(email.lower() for email in emails if email))
    
    def is_domain_participant(self, transcript: Dict) -> bool:
        """Check if transcript has participants from the target domain."""
        participant_emails = self.extract_participant_emails(transcript)
        
        for email in participant_emails:
            if email.endswith(f"@{self.domain}"):
                logger.debug(f"Found domain participant: {email}")
                return True
                
        return False
    
    def fetch_domain_meetings(self) -> List[Dict]:
        """Fetch meetings with participants from target domain (optimized)."""
        print(f"FlyCast: Searching for meetings with @{self.domain} participants...")
        logger.info(f"Fetching meetings for domain: {self.domain}")
        
        # Calculate date range
        from_date = datetime.now() - timedelta(days=self.days_back)
        
        all_transcripts = []
        limit = 10  # Smaller batch size for faster responses
        skip = 0
        found_domain_meetings = 0
        max_to_check = 150  # Reasonable limit to prevent excessive API calls
        
        while skip < max_to_check:
            try:
                query = """
                query MyTranscripts($limit: Int, $skip: Int) {
                  transcripts(limit: $limit, skip: $skip, mine: true) {
                    id
                    title
                    dateString
                    date
                    transcript_url
                    host_email
                    organizer_email
                    participants
                    fireflies_users
                    meeting_attendees {
                      email
                      name
                      displayName
                    }
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
                
                variables = {"limit": limit, "skip": skip}
                
                logger.debug(f"Fetching batch: skip={skip}, limit={limit}")
                data = self.fireflies_api.execute_query(query, variables)
                
                if not data or 'transcripts' not in data:
                    break
                    
                batch = data['transcripts']
                if not batch:
                    break
                    
                # Filter this batch for domain participants
                for transcript in batch:
                    # Filter by date
                    date_str = transcript.get('dateString') or transcript.get('date')
                    if date_str:
                        try:
                            meeting_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            if meeting_date < from_date:
                                # If we've gone past our date range, we can stop entirely
                                print(f"FlyCast: Reached meetings older than {self.days_back} days, stopping search...")
                                skip = max_to_check  # Force exit from outer loop
                                break
                        except:
                            pass
                    
                    if self.is_domain_participant(transcript):
                        all_transcripts.append(transcript)
                        found_domain_meetings += 1
                        logger.info(f"Found meeting with {self.domain} participant: {transcript.get('title', 'Unknown')}")
                        print(f"✅ Found: {transcript.get('title', 'Unknown')} ({date_str})")
                
                skip += limit
                
                # Show progress
                if skip % 30 == 0 and batch:
                    oldest_date = batch[-1].get('dateString', 'Unknown')
                    print(f"FlyCast: Checked {skip} meetings so far...")
                
                # Don't stop early - continue until we've checked all meetings in date range
                # This ensures we capture all meetings within the specified time period
                
                if len(batch) < limit:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching transcripts: {e}")
                print(f"FlyCast Error: Failed to fetch meetings: {str(e)}")
                break
        
        if not all_transcripts:
            print(f"FlyCast: No meetings found with @{self.domain} participants")
            return []
        
        # Sort by date (oldest first for chronological narrative)
        all_transcripts.sort(key=lambda x: x.get('date', '') or x.get('dateString', ''))
        
        print(f"FlyCast: Found {len(all_transcripts)} meetings with @{self.domain} participants")
        return all_transcripts
    
    def prepare_for_gemini(self, transcripts: List[Dict]) -> str:
        """Prepare transcript data for Gemini prompt."""
        content_parts = []
        
        for transcript in transcripts:
            meeting_info = []
            meeting_info.append(f"MEETING: {transcript.get('title', 'Untitled')}")
            meeting_info.append(f"DATE: {transcript.get('dateString', 'Unknown date')}")
            meeting_info.append(f"URL: {transcript.get('transcript_url', 'No URL')}")
            
            # Add participant info
            participant_emails = self.extract_participant_emails(transcript)
            domain_participants = [e for e in participant_emails if e.endswith(f"@{self.domain}")]
            if domain_participants:
                meeting_info.append(f"DOMAIN PARTICIPANTS: {', '.join(domain_participants)}")
            
            # Add summary if available
            summary = transcript.get('summary', {})
            if summary and summary.get('overview'):
                meeting_info.append(f"\nSUMMARY:\n{summary['overview']}")
            
            # Extract key discussion points
            sentences = transcript.get('sentences', [])[:200]  # First 200 sentences
            if sentences:
                # Group sentences by speaker
                speaker_segments = {}
                for sentence in sentences:
                    if sentence and sentence.get('text'):
                        speaker = sentence.get('speaker_name', 'Unknown')
                        if speaker not in speaker_segments:
                            speaker_segments[speaker] = []
                        speaker_segments[speaker].append(sentence['text'])
                
                # Add a sample of the conversation
                meeting_info.append("\nKEY DISCUSSION EXCERPTS:")
                excerpt_count = 0
                for speaker, texts in speaker_segments.items():
                    if excerpt_count >= 10:  # Limit excerpts
                        break
                    # Find substantive statements (not just short responses)
                    for text in texts:
                        if len(text) > 50 and excerpt_count < 10:
                            meeting_info.append(f"- {speaker}: {text}")
                            excerpt_count += 1
            
            content_parts.append("\n".join(meeting_info))
            content_parts.append("\n" + "="*80 + "\n")
        
        return "\n".join(content_parts)
    
    def generate(self):
        """Main method to generate the case study."""
        # Fetch domain meetings
        domain_meetings = self.fetch_domain_meetings()
        
        if not domain_meetings:
            return None
        
        # Prepare content for Gemini
        print("\nFlyCast: Preparing meeting data...")
        transcripts_content = self.prepare_for_gemini(domain_meetings)
        
        # Generate case study with Gemini
        print("FlyCast: Generating case study with AI...")
        prompt = CASE_STUDY_PROMPT.format(
            domain=self.domain,
            transcripts=transcripts_content
        )
        
        try:
            response = self.model.generate_content(prompt)
            case_study = response.text
            
            # Copy to clipboard
            subprocess.run(['pbcopy'], input=case_study.encode(), check=True)
            
            print("\n✅ FlyCast: Case study generated and copied to clipboard!")
            print("\n" + "="*60)
            print(case_study)
            
            return case_study
            
        except Exception as e:
            logger.error(f"Failed to generate case study: {e}")
            print(f"FlyCast Error: Failed to generate case study: {e}")
            return None


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        domain = input("Client domain (e.g., acme.com): ").strip()
    else:
        domain = sys.argv[1]
    
    days_back = 180  # Default
    if len(sys.argv) > 2:
        try:
            days_back = int(sys.argv[2])
        except ValueError:
            print("Warning: Invalid days_back value, using default of 180")
    
    try:
        generator = OptimizedCaseStudyGenerator(domain, days_back)
        generator.generate()
    except Exception as e:
        print(f"FlyCast Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()