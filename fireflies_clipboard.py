#!/usr/bin/env python3

import os
import sys
import requests
import datetime
from dateutil import parser as date_parser
import pyperclip  # pip install pyperclip
import subprocess
import time
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(dotenv_path=env_path)

# Get API key from environment
FIREFLIES_API_KEY = os.environ.get("FIREFLIES_API_KEY", "")
GRAPHQL_ENDPOINT = "https://api.fireflies.ai/graphql"

def main():
    if not FIREFLIES_API_KEY:
        print("Error: FIREFLIES_API_KEY not set.")
        sys.exit(1)

    # Query transcripts from the last 7 days.
    now = datetime.datetime.now(datetime.timezone.utc)
    from_date_str = (now - datetime.timedelta(days=7)).isoformat() + "Z"
    to_date_str = now.isoformat() + "Z"

    query = """
    query MyTranscripts($limit: Int) {
      transcripts(limit: $limit, mine: true) {
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

    variables = {"limit": 5}  # or however many you want to fetch
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FIREFLIES_API_KEY}"
    }

    resp = requests.post(GRAPHQL_ENDPOINT, 
                         json={"query": query, "variables": variables}, 
                         headers=headers)
    if resp.status_code != 200:
        print(f"Request error: {resp.status_code} - {resp.text}")
        sys.exit(1)

    data = resp.json()
    transcripts = data.get("data", {}).get("transcripts", [])
    if not transcripts:
        print("No transcripts found.")
        return

    # Sort by date descending
    transcripts.sort(key=lambda t: date_parser.isoparse(t["dateString"]), reverse=True)
    newest = transcripts[0]

    # Build text
    lines = []
    lines.append(f"=== {newest['title']} ({newest['dateString']}) ===")
    
    overview = newest["summary"].get("overview", "")
    if overview:
        lines.append(f"Summary: {overview}\n")
    
    lines.append("Transcript:")
    for s in newest["sentences"]:
        speaker = s.get("speaker_name", "Unknown")
        text = s.get("text") or s.get("raw_text") or ""
        lines.append(f"{speaker}: {text}")
    
    final_text = "\n".join(lines)
    pyperclip.copy(final_text)
    # Add a small delay to ensure the clipboard is updated
    time.sleep(0.1)
    
    # Try to paste, but handle failures gracefully
    try:
        # Use AppleScript to simulate cmd+v
        result = subprocess.run(
            ['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("Copied and pasted Fireflies transcript successfully!")
        else:
            print(f"Copied Fireflies transcript to clipboard. Paste manually with Cmd+V.")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Copied Fireflies transcript to clipboard. Paste manually with Cmd+V.")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()