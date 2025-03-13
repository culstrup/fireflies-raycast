#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Fetch Fireflies Transcripts from Chrome
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 📋
# @raycast.packageName Fireflies

# Documentation:
# @raycast.description Fetch Fireflies transcripts from Chrome tabs, copy to clipboard, and paste (requires accessibility permissions)
# @raycast.author christian_ulstrup
# @raycast.authorURL https://raycast.com/christian_ulstrup

# Setup the environment and run the script
source "$(dirname "$0")/.venv/bin/activate"
python3 "$(dirname "$0")/fetch_fireflies_from_chrome_tabs.py" --paste