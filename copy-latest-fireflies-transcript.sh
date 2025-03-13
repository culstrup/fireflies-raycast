#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Copy Latest Fireflies Transcript
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 📝
# @raycast.packageName Fireflies

# Documentation:
# @raycast.description Copies the most recent Fireflies transcript to clipboard and attempts to paste
# @raycast.author christian_ulstrup
# @raycast.authorURL https://raycast.com/christian_ulstrup

# Setup the environment and run the script
source "$(dirname "$0")/.venv/bin/activate"
python3 "$(dirname "$0")/fireflies_clipboard.py"