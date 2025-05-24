#!/usr/bin/env python3

import logging
import subprocess
import sys
import time
import traceback

import pyperclip
from dateutil import parser as date_parser

from fireflies_api import FirefliesAPI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("fireflies_clipboard")


def setup_clipboard(content):
    """
    Copy content to clipboard and optionally paste it.

    Args:
        content: Text content to copy to clipboard
    """
    try:
        # Copy to clipboard
        pyperclip.copy(content)
        # Add a small delay to ensure the clipboard is updated
        time.sleep(0.1)

        # Try to paste, but handle failures gracefully
        try:
            # Use AppleScript to simulate cmd+v
            result = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info("Copied and pasted Fireflies transcript successfully!")
                print("Copied and pasted Fireflies transcript successfully!")
            else:
                logger.warning(f"Failed to paste: {result.stderr}")
                print("Copied Fireflies transcript to clipboard. Paste manually with Cmd+V.")
        except Exception as e:
            logger.error(f"Error while pasting: {e}")
            print("Copied Fireflies transcript to clipboard. Paste manually with Cmd+V.")
    except Exception as e:
        logger.error(f"Error copying to clipboard: {e}")
        logger.error(traceback.format_exc())
        print(f"Error: Failed to copy transcript to clipboard: {str(e)}")
        sys.exit(1)


def main():
    """Main function to fetch and copy the latest Fireflies transcript."""
    try:
        # Initialize Fireflies API
        api = None
        try:
            api = FirefliesAPI()
        except ValueError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

        # Safety check
        if api is None:
            print("Failed to initialize Fireflies API")
            sys.exit(1)

        # Get recent transcripts
        try:
            transcripts = api.get_recent_transcripts(limit=5)
        except ValueError as e:
            print(f"Error fetching transcripts: {str(e)}")
            sys.exit(1)

        if not transcripts:
            print("No transcripts found.")
            return

        # Sort by date descending
        try:
            transcripts.sort(key=lambda t: date_parser.isoparse(t["dateString"]), reverse=True)
            newest = transcripts[0]
        except Exception as e:
            logger.error(f"Error sorting transcripts: {e}")
            print(f"Error processing transcripts: {str(e)}")
            sys.exit(1)

        # Check if the transcript is still processing
        sentences = newest.get("sentences", [])
        if not sentences:
            print(
                f"The latest meeting '{newest.get('title', 'Unknown')}' "
                "is still processing. Transcript not available yet."
            )
            return

        # Format the transcript
        formatted_text = api.format_transcript(newest)

        # Copy and optionally paste
        setup_clipboard(formatted_text)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
