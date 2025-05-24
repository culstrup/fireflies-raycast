#!/usr/bin/env python3

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from generate_case_study_optimized import OptimizedCaseStudyGenerator

# Test with agentgrid.net for 60 days
generator = OptimizedCaseStudyGenerator("agentgrid.net", days_back=60)

# Calculate the cutoff date
cutoff_date = datetime.now() - timedelta(days=60)
print(f"Looking for meetings after: {cutoff_date.strftime('%Y-%m-%d')}")
print(f"Today is: {datetime.now().strftime('%Y-%m-%d')}")

# Get meetings
meetings = generator.fetch_domain_meetings()

print(f"\nFound {len(meetings)} meetings total")
print("\nMeetings in chronological order:")
for i, m in enumerate(meetings):
    date = m.get("dateString", "Unknown")
    title = m.get("title", "Unknown")

    # Parse date to check if it's in April
    if "2025-04" in date:
        print(f"{i+1}. {date} - {title} ✅ APRIL MEETING")
