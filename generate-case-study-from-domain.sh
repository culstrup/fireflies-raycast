#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Generate Case Study from Domain
# @raycast.mode fullOutput
# @raycast.packageName FlyCast

# Optional parameters:
# @raycast.icon 📊
# @raycast.description Generate AI case study from all meetings with a client domain
# @raycast.author Christian Ulstrup
# @raycast.authorURL https://github.com/culstrup

# Arguments:
# @raycast.argument1 { "type": "text", "placeholder": "Client domain (e.g., acme.com)" }
# @raycast.argument2 { "type": "text", "placeholder": "Days back (default: 180)", "optional": true }

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "FlyCast Error: Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check for required API keys
if [ -z "$FIREFLIES_API_KEY" ]; then
    echo "FlyCast Error: FIREFLIES_API_KEY not found in .env file"
    echo "Please add your Fireflies API key to the .env file"
    exit 1
fi

if [ -z "$GOOGLE_AI_STUDIO_KEY" ]; then
    echo "FlyCast Error: GOOGLE_AI_STUDIO_KEY not found in .env file"
    echo "Please add your Google AI Studio API key to the .env file"
    exit 1
fi

# Set default days back if not provided
DAYS_BACK="${2:-180}"

# Run the full Python script with arguments (includes complete transcripts)
python3 generate_case_study_from_domain.py "$1" "$DAYS_BACK" 2>&1

# Check exit status
if [ $? -eq 0 ]; then
    # Play success sound
    afplay /System/Library/Sounds/Glass.aiff 2>/dev/null &
else
    # Play error sound
    afplay /System/Library/Sounds/Basso.aiff 2>/dev/null &
fi
