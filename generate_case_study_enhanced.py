#!/usr/bin/env python3

import json
import logging
import os
import sys

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import google.generativeai as genai

from fireflies_api import FirefliesAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EnhancedCaseStudyGenerator:
    """Generate case studies by mapping domains to known participant names."""

    def __init__(self, domain: str, days_back: int = 180):
        self.domain = domain.lower().strip()
        self.days_back = days_back
        self.fireflies_api = FirefliesAPI()

        # Configure Gemini
        api_key = os.getenv("GOOGLE_AI_STUDIO_KEY")
        if not api_key:
            raise ValueError("GOOGLE_AI_STUDIO_KEY not found in environment")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-pro-latest")

        # Load domain-to-participants mapping
        self.domain_participants = self._load_domain_mapping()

    def _load_domain_mapping(self) -> dict[str, list[str]]:
        """Load domain to participant names mapping."""
        mapping_file = os.path.join(os.path.dirname(__file__), "domain_participants.json")
        if os.path.exists(mapping_file):
            with open(mapping_file) as f:
                return json.load(f)
        return {}

    def get_participants_for_domain(self) -> list[str]:
        """Get known participant names for the domain."""
        return self.domain_participants.get(self.domain, [])

    def find_meetings_by_participants(self, participants: list[str]) -> list[dict]:
        """Find all meetings where any of the participants were present."""
        all_meetings = []
        seen_ids = set()

        for participant in participants:
            print(f"🔍 Searching for meetings with {participant}...")

            query = """
            query MyTranscripts($limit: Int, $skip: Int) {
              transcripts(limit: $limit, skip: $skip, mine: true) {
                id
                title
                dateString
                date
                transcript_url
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

            skip = 0
            limit = 10
            max_meetings = 300  # Limit search to prevent timeouts

            while skip < max_meetings:
                try:
                    data = self.fireflies_api.execute_query(query, {"limit": limit, "skip": skip})

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
                        if sentences:
                            for sentence in sentences:
                                if sentence and sentence.get("speaker_name"):
                                    speakers.add(sentence["speaker_name"])

                        # Check if our participant is in this meeting
                        for speaker in speakers:
                            if participant.lower() in speaker.lower():
                                # Avoid duplicates
                                if transcript["id"] not in seen_ids:
                                    seen_ids.add(transcript["id"])
                                    all_meetings.append(transcript)
                                    print(f"✅ Found: {transcript['title']}")
                                break

                    skip += limit

                    if len(batch) < limit:
                        break

                except Exception as e:
                    logger.error(f"Error searching for {participant}: {e}")
                    break

        # Sort by date
        all_meetings.sort(key=lambda x: x.get("date", ""), reverse=True)
        return all_meetings

    def prepare_for_gemini(self, meetings: list[dict]) -> str:
        """Prepare meeting data for Gemini prompt."""
        content = []

        for meeting in meetings:
            content.append(f"Meeting: {meeting['title']}")
            content.append(f"Date: {meeting.get('dateString', 'Unknown')}")

            # Add summary if available
            summary = meeting.get("summary", {})
            if summary and summary.get("overview"):
                content.append(f"Summary: {summary['overview']}")

            # Extract key discussion points from sentences
            sentences = meeting.get("sentences", [])[:100]  # First 100 sentences
            if sentences:
                discussion_points = []
                for sentence in sentences:
                    if sentence and sentence.get("text"):
                        text = sentence["text"]
                        # Look for key phrases
                        if any(
                            keyword in text.lower()
                            for keyword in ["challenge", "solution", "implement", "result", "success", "problem"]
                        ):
                            discussion_points.append(text)

                if discussion_points:
                    content.append("Key Discussion Points:")
                    for point in discussion_points[:10]:  # Limit to 10 key points
                        content.append(f"- {point}")

            content.append("\n" + "=" * 50 + "\n")

        return "\n".join(content)

    def generate_case_study(self):
        """Main method to generate the case study."""
        # Get participants for this domain
        participants = self.get_participants_for_domain()

        if not participants:
            print(f"❌ No known participants for domain {self.domain}")
            print("💡 Add participant names to domain_participants.json")
            return None

        print(f"📋 Known participants for {self.domain}: {', '.join(participants)}")

        # Find meetings
        meetings = self.find_meetings_by_participants(participants)

        if not meetings:
            print(f"❌ No meetings found with {self.domain} participants")
            return None

        print(f"\n✅ Found {len(meetings)} meetings with {self.domain} participants")

        # Prepare content for Gemini
        meeting_content = self.prepare_for_gemini(meetings)

        # Generate case study
        print("\n🤖 Generating case study with Gemini...")

        prompt = f"""Based on the following meeting transcripts with {self.domain} participants,
create a compelling case study that showcases our work together.

Focus on:
1. The client's challenges and needs
2. Our approach and solutions
3. Key outcomes and successes
4. Specific examples and quotes where relevant

Make it professional, engaging, and suitable for marketing purposes.

CLIENT DOMAIN: {self.domain}

MEETING TRANSCRIPTS:
{meeting_content}"""

        try:
            response = self.model.generate_content(prompt)
            case_study = response.text

            # Copy to clipboard
            import subprocess

            subprocess.run(["pbcopy"], input=case_study.encode(), check=True)

            print("\n✅ Case study generated and copied to clipboard!")
            print("\n" + "=" * 60)
            print(case_study[:500] + "...")

            return case_study

        except Exception as e:
            logger.error(f"Failed to generate case study: {e}")
            print(f"❌ Error generating case study: {e}")
            return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_case_study_enhanced.py <domain>")
        print("Example: python generate_case_study_enhanced.py fpt.org.pl")
        sys.exit(1)

    domain = sys.argv[1]
    generator = EnhancedCaseStudyGenerator(domain)
    generator.generate_case_study()
