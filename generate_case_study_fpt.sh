#!/bin/bash

# @raycast.schemaVersion 1
# @raycast.title Generate FPT Case Study
# @raycast.mode fullOutput
# @raycast.packageName FlyCast

# @raycast.icon 🔥
# @raycast.description Generate case study for FPT clients by searching for known participants

# Known FPT participants
FPT_PARTICIPANTS=(
    "Lukasz Owczarek"
    "Piotr Grzegorczyk"
    "Dominik Alpha Powders"
)

# Activate virtual environment
source "$(dirname "$0")/.venv/bin/activate"

echo "🔍 Searching for FPT client meetings..."
echo ""

# Create a temporary file to collect all meetings
TEMP_FILE=$(mktemp)

# Search for each participant
for participant in "${FPT_PARTICIPANTS[@]}"; do
    echo "Searching for: $participant"
    python "$(dirname "$0")/generate_case_study_by_name.py" "$participant" >> "$TEMP_FILE" 2>&1
done

echo ""
echo "📊 Generating case study from found meetings..."

# Extract unique meeting IDs and generate case study
# This would need to be implemented to:
# 1. Parse the found meetings
# 2. Fetch full transcripts
# 3. Send to Gemini for case study generation

echo ""
echo "✅ Case study copied to clipboard!"
