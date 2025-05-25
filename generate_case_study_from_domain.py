#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import time
import traceback
from datetime import datetime, timedelta

import google.generativeai as genai
import pyperclip
from dateutil import parser as date_parser

from fireflies_api import FirefliesAPI

# Setup logging
script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, "debug.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
)

logger = logging.getLogger("case_study_generator")

# Case study prompt template
CASE_STUDY_PROMPT = """
You are creating a professional case study from client meeting transcripts.

Client Domain: {domain}
Number of Meetings: {meeting_count}
Date Range: {start_date} to {end_date}

Transcripts are provided in chronological order below.

Create a compelling case study that includes:
1. Executive Summary
2. Client Challenge/Problem Statement
3. Solution Journey (based on meeting progression)
4. Key Milestones and Decisions
5. Results and Outcomes
6. Client Testimonials (extract actual quotes when available)
7. Lessons Learned

Important guidelines:
- Use actual quotes from the transcripts when possible
- Highlight the progression and evolution across meetings
- Focus on business value and outcomes
- Keep the tone professional but engaging
- Format as markdown suitable for publication

MEETING TRANSCRIPTS:
{transcripts}
"""


class DomainCaseStudyGenerator:
    """Generate case studies from meetings filtered by participant domain."""

    def __init__(self, domain: str, days_back: int = 180):
        """
        Initialize the case study generator.

        Args:
            domain: Email domain to filter by (e.g., 'acme.com')
            days_back: Number of days to look back for meetings
        """
        self.domain = domain.lower().strip()
        if not self.domain:
            raise ValueError("Domain cannot be empty")

        self.days_back = days_back
        self.fireflies_api = FirefliesAPI()

        # Configure Gemini
        api_key = os.getenv("GOOGLE_AI_STUDIO_KEY")
        if not api_key:
            logger.error("GOOGLE_AI_STUDIO_KEY not found in environment")
            raise ValueError("GOOGLE_AI_STUDIO_KEY not set. Please add it to your .env file.")

        genai.configure(api_key=api_key)

        # Use Gemini 2.5 Pro Preview
        try:
            self.model = genai.GenerativeModel("gemini-2.5-pro-preview-05-06")
            logger.info("Initialized Gemini 2.5 Pro Preview model")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini 2.5 Pro: {e}")
            try:
                self.model = genai.GenerativeModel("gemini-1.5-pro")
                logger.info("Fell back to Gemini 1.5 Pro model")
            except Exception:
                self.model = genai.GenerativeModel("gemini-pro")
                logger.info("Fell back to gemini-pro model")

    def extract_participant_emails(self, transcript: dict) -> list[str]:
        """
        Extract all participant emails from a transcript.

        Args:
            transcript: Transcript data from Fireflies API

        Returns:
            List of email addresses found in the transcript
        """
        emails = []

        # Extract from participants array (primary source of emails!)
        participants = transcript.get("participants", []) or []
        for participant in participants:
            if participant and isinstance(participant, str):
                # Handle comma-separated emails in single string
                if "," in participant:
                    emails.extend([e.strip() for e in participant.split(",") if "@" in e])
                elif "@" in participant:
                    emails.append(participant)

        # Extract from meeting_attendees (detailed attendee info)
        attendees = transcript.get("meeting_attendees", []) or []
        for attendee in attendees:
            if attendee and isinstance(attendee, dict) and attendee.get("email"):
                emails.append(attendee["email"])

        # Check host email
        host_email = transcript.get("host_email", "") or ""
        if host_email and "@" in host_email:
            emails.append(host_email)

        # Check organizer email
        organizer_email = transcript.get("organizer_email", "") or ""
        if organizer_email and "@" in organizer_email:
            emails.append(organizer_email)

        # Also check fireflies_users
        ff_users = transcript.get("fireflies_users", []) or []
        for user in ff_users:
            if user and "@" in user:
                emails.append(user)

        # Deduplicate and return
        return list(set(email.lower() for email in emails if email))

    def is_domain_participant(self, transcript: dict) -> bool:
        """
        Check if transcript has participants from the target domain.

        Args:
            transcript: Transcript data from Fireflies API

        Returns:
            True if domain participants found, False otherwise
        """
        participant_emails = self.extract_participant_emails(transcript)

        for email in participant_emails:
            if email.endswith(f"@{self.domain}"):
                logger.debug(f"Found domain participant: {email}")
                return True

        return False

    def fetch_domain_meetings(self) -> list[dict]:
        """
        Fetch all meetings with participants from target domain.

        Returns:
            List of transcript objects sorted by date
        """
        print(f"FlyCast: Searching for meetings with @{self.domain} participants...")
        logger.info(f"Fetching meetings for domain: {self.domain}")

        # Calculate date range
        from_date = datetime.now() - timedelta(days=self.days_back)
        from_date.strftime("%Y-%m-%d")

        # Fetch transcripts with pagination but WITHOUT fromDate filter
        # The API seems to not return older meetings when fromDate is used
        all_transcripts = []
        limit = 30  # Reduced to avoid timeouts
        skip = 0
        found_domain_meetings = 0

        while True:
            try:
                # Remove fromDate filter to get ALL meetings
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

                if not data or "transcripts" not in data:
                    break

                batch = data["transcripts"]
                if not batch:
                    break

                # Filter this batch for domain participants
                batch_domain_meetings = []
                should_stop = False

                for transcript in batch:
                    # Filter by date FIRST, before checking domain
                    date_str = transcript.get("dateString") or transcript.get("date")
                    if date_str:
                        try:
                            meeting_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            if meeting_date < from_date:
                                # Since results are sorted by date desc, if we hit an old meeting,
                                # all subsequent meetings will also be old
                                should_stop = True
                                logger.info(f"Hit meeting from {meeting_date}, stopping search")
                                break
                        except Exception:
                            pass  # If date parsing fails, include the meeting

                    # Only check domain if within date range
                    if self.is_domain_participant(transcript):
                        batch_domain_meetings.append(transcript)
                        found_domain_meetings += 1

                all_transcripts.extend(batch_domain_meetings)

                # Stop fetching if we've gone past our date range
                if should_stop:
                    logger.info(f"Reached meetings older than {self.days_back} days, stopping search")
                    break

                # If we got fewer than the limit, we've reached the end
                if len(batch) < limit:
                    break

                skip += limit

                # Show progress - also show the date range we've covered
                if batch and not should_stop:
                    oldest_date = batch[-1].get("dateString", "Unknown")
                    newest_date = batch[0].get("dateString", "Unknown")
                    print(
                        f"FlyCast: Batch covers {newest_date[:10]} to {oldest_date[:10]}, "
                        f"found {found_domain_meetings} @{self.domain} meetings so far..."
                    )

                # Early exit if we have enough meetings
                if found_domain_meetings >= 20:  # Reasonable limit for case study
                    print(f"FlyCast: Found sufficient meetings ({found_domain_meetings}), stopping search...")
                    break

                # Also exit if we've searched too many meetings
                if skip >= 600:  # Reasonable limit to prevent infinite loops
                    print(f"FlyCast: Searched {skip} meetings, stopping to prevent timeout...")
                    break

            except Exception as e:
                logger.error(f"Error fetching transcripts: {e}")
                print(f"FlyCast Error: Failed to fetch meetings: {str(e)}")
                raise

        logger.info(f"Found {len(all_transcripts)} meetings with @{self.domain} participants")

        # Sort by date (oldest first for chronological narrative)
        all_transcripts.sort(key=lambda x: self._parse_date(x), reverse=False)

        return all_transcripts

    def _parse_date(self, transcript: dict) -> datetime:
        """Parse date from transcript data."""
        # Try dateString first
        date_str = transcript.get("dateString", "")
        if date_str:
            try:
                return date_parser.parse(date_str)
            except Exception:
                pass

        # Fall back to timestamp
        timestamp = transcript.get("date", 0)
        if timestamp:
            return datetime.fromtimestamp(timestamp / 1000)  # Convert from milliseconds

        # Default to now if no date found
        return datetime.now()

    def prepare_for_gemini(self, transcripts: list[dict]) -> tuple[str, dict[str, any]]:
        """
        Format transcripts for Gemini processing.

        Args:
            transcripts: List of transcript objects

        Returns:
            Formatted content string and metadata dict
        """
        print("FlyCast: Preparing transcript context (this may take a moment)...")

        if not transcripts:
            raise ValueError("No transcripts to process")

        # Calculate date range
        dates = [self._parse_date(t) for t in transcripts]
        start_date = min(dates).strftime("%B %d, %Y")
        end_date = max(dates).strftime("%B %d, %Y")

        # Format each transcript
        formatted_transcripts = []
        total_chars = 0
        max_chars = 1_500_000  # Leave room for prompt and response

        for i, transcript in enumerate(transcripts):
            try:
                meeting_date = self._parse_date(transcript).strftime("%B %d, %Y")
                title = transcript.get("title", f"Meeting {i+1}")

                # Start with meeting header
                meeting_text = f"\n{'='*80}\n"
                meeting_text += f"MEETING {i+1}: {title}\n"
                meeting_text += f"Date: {meeting_date}\n"
                meeting_text += f"URL: {transcript.get('transcript_url', 'N/A')}\n"

                # Add summary if available
                summary_obj = transcript.get("summary") or {}
                if isinstance(summary_obj, dict):
                    summary = summary_obj.get("overview", "")
                    if summary:
                        meeting_text += f"\nSummary: {summary}\n"

                meeting_text += f"\nTranscript:\n{'-'*40}\n"

                # Add transcript content
                sentences = transcript.get("sentences") or []
                if sentences and isinstance(sentences, list):
                    for sentence in sentences:
                        if isinstance(sentence, dict):
                            speaker = sentence.get("speaker_name", "Unknown")
                            text = sentence.get("text") or sentence.get("raw_text", "")
                            if text:
                                meeting_text += f"{speaker}: {text}\n"
                else:
                    meeting_text += "[No transcript content available]\n"

                # Check if adding this would exceed our limit
                if total_chars + len(meeting_text) > max_chars:
                    logger.warning(f"Truncating at meeting {i+1} due to token limits")
                    meeting_text = f"\n[Remaining {len(transcripts) - i} meetings truncated due to length limits]\n"
                    formatted_transcripts.append(meeting_text)
                    break

                formatted_transcripts.append(meeting_text)
                total_chars += len(meeting_text)

            except Exception as e:
                logger.error(f"Error processing transcript {i+1}: {e}")
                logger.error(f"Transcript data: {transcript}")
                # Skip this transcript but continue with others
                continue

        content = "".join(formatted_transcripts)

        metadata = {
            "domain": self.domain,
            "meeting_count": len(transcripts),
            "start_date": start_date,
            "end_date": end_date,
            "total_chars": total_chars,
            "truncated": len(formatted_transcripts) < len(transcripts),
        }

        logger.info(f"Prepared {len(formatted_transcripts)} meetings, {total_chars} chars")

        return content, metadata

    def generate_case_study(self, formatted_content: str, metadata: dict) -> str:
        """
        Send to Gemini and generate case study.

        Args:
            formatted_content: Formatted transcript content
            metadata: Metadata about the meetings

        Returns:
            Generated case study text
        """
        print("FlyCast: Generating case study with Gemini 2.5 Pro...")

        # Fill in the prompt template
        prompt = CASE_STUDY_PROMPT.format(
            domain=metadata["domain"],
            meeting_count=metadata["meeting_count"],
            start_date=metadata["start_date"],
            end_date=metadata["end_date"],
            transcripts=formatted_content,
        )

        try:
            logger.info("Sending request to Gemini API")
            start_time = time.time()

            # Generate content
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                ),
            )

            generation_time = time.time() - start_time
            logger.info(f"Gemini generation completed in {generation_time:.2f}s")
            print(f"FlyCast: Case study generated in {generation_time:.2f}s")

            return response.text

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            logger.error(traceback.format_exc())
            raise ValueError(f"Failed to generate case study: {str(e)}") from e

    def run(self) -> str:
        """
        Execute the full workflow and return the case study.

        Returns:
            Generated case study text
        """
        try:
            # Fetch domain meetings
            meetings = self.fetch_domain_meetings()

            if not meetings:
                message = f"No meetings found with participants from @{self.domain}"
                print(f"FlyCast: {message}")
                return message

            print(f"FlyCast: Found {len(meetings)} meetings spanning {self.days_back} days")

            # Prepare for Gemini
            content, metadata = self.prepare_for_gemini(meetings)

            # Generate case study
            case_study = self.generate_case_study(content, metadata)

            return case_study

        except Exception as e:
            logger.error(f"Error in case study generation: {e}")
            logger.error(traceback.format_exc())
            raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Generate AI case study from client meeting transcripts")
    parser.add_argument("domain", help="Client email domain to filter by (e.g., acme.com)")
    parser.add_argument(
        "days_back", nargs="?", type=int, default=180, help="Number of days to look back (default: 180)"
    )
    parser.add_argument(
        "--output",
        choices=["clipboard", "stdout", "file"],
        default="clipboard",
        help="Where to output the case study (default: clipboard)",
    )
    parser.add_argument("--output-file", help="File path when using --output file")

    args = parser.parse_args()

    try:
        # Create generator
        generator = DomainCaseStudyGenerator(args.domain, args.days_back)

        # Generate case study
        case_study = generator.run()

        # Output based on preference
        if args.output == "clipboard":
            pyperclip.copy(case_study)
            print("\nFlyCast: Case study copied to clipboard!")
            print("FlyCast: Paste it anywhere with Cmd+V")
        elif args.output == "stdout":
            print("\n" + "=" * 80)
            print(case_study)
        elif args.output == "file":
            output_path = args.output_file or f"case_study_{args.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(output_path, "w") as f:
                f.write(case_study)
            print(f"\nFlyCast: Case study saved to {output_path}")

    except KeyboardInterrupt:
        print("\nFlyCast: Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFlyCast Error: {str(e)}")
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

    # Script completed successfully
    logger.info("Script completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
