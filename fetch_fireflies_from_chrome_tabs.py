#!/usr/bin/env python3

import os
import sys
import re
import requests
import pyperclip
import subprocess
import time
import traceback
import logging
import argparse
from dotenv import load_dotenv
from pathlib import Path

# Setup logging
script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, "debug.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fireflies_script")

# Load environment variables from .env file
try:
    env_path = os.path.join(script_dir, ".env")
    logger.info(f"Looking for .env file at: {env_path}")
    if not os.path.exists(env_path):
        logger.error(f".env file not found at {env_path}")
    load_dotenv(dotenv_path=env_path)
    logger.info("Environment variables loaded")
except Exception as e:
    logger.error(f"Error loading .env file: {e}")
    logger.error(traceback.format_exc())

# Configuration
FIREFLIES_API_KEY = os.environ.get("FIREFLIES_API_KEY", "")
if not FIREFLIES_API_KEY:
    logger.error("FIREFLIES_API_KEY environment variable not set")
else:
    logger.info("API key loaded successfully")
    
GRAPHQL_ENDPOINT = "https://api.fireflies.ai/graphql"

def get_chrome_tabs():
    """Get URLs from all open Chrome tabs"""
    try:
        logger.info("Getting Chrome tabs with Fireflies URLs")
        apple_script = '''
        tell application "Google Chrome"
            set tabList to {}
            set windowList to every window
            repeat with theWindow in windowList
                set tabList to tabList & (every tab of theWindow whose URL contains "fireflies.ai/view/")
            end repeat
            set urlList to {}
            repeat with theTab in tabList
                set the end of urlList to URL of theTab
            end repeat
            return urlList
        end tell
        '''
        result = subprocess.run(['osascript', '-e', apple_script], 
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"AppleScript error: {result.stderr}")
            return []
            
        urls = result.stdout.strip().split(", ")
        filtered_urls = [url for url in urls if url]
        logger.info(f"Found {len(filtered_urls)} Chrome tabs with Fireflies URLs")
        logger.debug(f"URLs found: {filtered_urls}")
        return filtered_urls
    except Exception as e:
        logger.error(f"Error getting Chrome tabs: {e}")
        logger.error(traceback.format_exc())
        return []

def extract_transcript_ids(urls):
    """Extract transcript IDs from Fireflies URLs"""
    try:
        logger.info("Extracting transcript IDs from URLs")
        transcript_ids = []
        pattern = r"fireflies\.ai/view/.*::([A-Za-z0-9]+)"
        
        for url in urls:
            match = re.search(pattern, url)
            if match:
                transcript_ids.append(match.group(1))
                logger.debug(f"Extracted ID {match.group(1)} from {url}")
            else:
                logger.warning(f"No transcript ID found in URL: {url}")
        
        logger.info(f"Extracted {len(transcript_ids)} transcript IDs")
        return transcript_ids
    except Exception as e:
        logger.error(f"Error extracting transcript IDs: {e}")
        logger.error(traceback.format_exc())
        return []

def fetch_transcript(transcript_id):
    """Fetch transcript details using the Fireflies GraphQL API"""
    try:
        logger.info(f"Fetching transcript with ID: {transcript_id}")
        if not FIREFLIES_API_KEY:
            logger.error("Error: FIREFLIES_API_KEY not set.")
            return None

        query = """
        query GetTranscript($id: String!) {
          transcript(id: $id) {
            id
            title
            dateString
            transcript_url
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

        variables = {"id": transcript_id}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FIREFLIES_API_KEY}"
        }

        logger.debug(f"Sending GraphQL request for transcript: {transcript_id}")
        resp = requests.post(GRAPHQL_ENDPOINT, 
                            json={"query": query, "variables": variables}, 
                            headers=headers)
        
        if resp.status_code != 200:
            logger.error(f"Request error: {resp.status_code} - {resp.text}")
            return None

        data = resp.json()
        transcript = data.get("data", {}).get("transcript")
        
        if not transcript:
            logger.error(f"No transcript data found in response: {data}")
            return None
            
        logger.info(f"Successfully fetched transcript: {transcript.get('title', 'Untitled')}")
        return transcript
    except Exception as e:
        logger.error(f"Error fetching transcript {transcript_id}: {e}")
        logger.error(traceback.format_exc())
        return None

def format_transcript(transcript):
    """Format transcript data as readable text"""
    try:
        logger.info(f"Formatting transcript: {transcript.get('title', 'Untitled')}")
        if not transcript:
            logger.warning("Attempted to format empty transcript")
            return ""
            
        lines = []
        lines.append(f"=== {transcript['title']} ({transcript['dateString']}) ===")
        
        # Safely handle missing summary field
        if transcript.get("summary") is not None:
            overview = transcript["summary"].get("overview", "")
            if overview:
                lines.append(f"Summary: {overview}\n")
        else:
            logger.warning(f"No summary found for transcript: {transcript.get('title')}")
        
        sentences = transcript.get("sentences", [])
        lines.append("Transcript:")
        logger.info(f"Processing {len(sentences)} sentences")
        
        for s in sentences:
            speaker = s.get("speaker_name", "Unknown")
            text = s.get("text") or s.get("raw_text") or ""
            lines.append(f"{speaker}: {text}")
        
        result = "\n".join(lines)
        logger.info(f"Formatted transcript with {len(lines)} lines")
        return result
    except Exception as e:
        logger.error(f"Error formatting transcript: {e}")
        logger.error(traceback.format_exc())
        return f"Error formatting transcript: {str(e)}"

def attempt_paste():
    """Try to paste the content using AppleScript"""
    try:
        logger.info("Attempting to paste content with AppleScript")
        paste_result = subprocess.run(
            ['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down'],
            capture_output=True, text=True
        )
        
        if paste_result.returncode != 0:
            logger.error(f"Error pasting content: {paste_result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Exception during paste attempt: {e}")
        return False

def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Fetch Fireflies transcripts from Chrome tabs')
        parser.add_argument('--paste', action='store_true', help='Attempt to automatically paste content')
        args = parser.parse_args()
        
        logger.info("Script started")
        
        # Get all Chrome tabs with Fireflies URLs
        urls = get_chrome_tabs()
        if not urls:
            logger.error("No Fireflies tabs found in Chrome.")
            print("No Fireflies tabs found in Chrome.")
            sys.exit(1)
        
        # Extract transcript IDs
        transcript_ids = extract_transcript_ids(urls)
        if not transcript_ids:
            logger.error("No valid Fireflies transcript IDs found in Chrome tabs.")
            print("No valid Fireflies transcript IDs found in Chrome tabs.")
            sys.exit(1)
        
        logger.info(f"Found {len(transcript_ids)} Fireflies transcripts in Chrome tabs.")
        print(f"Found {len(transcript_ids)} Fireflies transcripts in Chrome tabs.")
        
        # Fetch and format each transcript
        all_transcripts = []
        for transcript_id in transcript_ids:
            logger.info(f"Processing transcript ID: {transcript_id}")
            transcript = fetch_transcript(transcript_id)
            if transcript:
                formatted = format_transcript(transcript)
                all_transcripts.append(formatted)
        
        if not all_transcripts:
            logger.error("Failed to fetch any transcripts")
            print("Failed to fetch any transcripts")
            sys.exit(1)
            
        # Combine all transcripts
        final_text = "\n\n" + "\n\n".join(all_transcripts)
        logger.info(f"Combined {len(all_transcripts)} transcripts, total size: {len(final_text)} characters")
        
        # Copy to clipboard
        logger.info("Copying to clipboard")
        pyperclip.copy(final_text)
        
        # Add a small delay to ensure the clipboard is updated
        time.sleep(0.1)
        
        # Try to paste if requested
        paste_success = False
        if args.paste:
            paste_success = attempt_paste()
            
        logger.info(f"Script completed successfully, copied {len(all_transcripts)} transcripts to clipboard")
        
        if paste_success:
            print(f"Copied and pasted {len(all_transcripts)} Fireflies transcripts successfully.")
        else:
            # If paste didn't work, it's still in the clipboard
            print(f"Copied {len(all_transcripts)} Fireflies transcripts to clipboard. Paste manually with Cmd+V.")
            
    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        logger.error(traceback.format_exc())
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()