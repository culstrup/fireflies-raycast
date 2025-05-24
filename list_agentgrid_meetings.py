#!/usr/bin/env python3

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from generate_case_study_optimized import OptimizedCaseStudyGenerator

# Test to see all agentgrid meetings in the last 45 days
print("Testing AgentGrid meeting detection...\n")

generator = OptimizedCaseStudyGenerator("agentgrid.net", days_back=45)
meetings = generator.fetch_domain_meetings()

print(f"\nTotal meetings found: {len(meetings)}")
print("\nMeetings in chronological order:")
for i, m in enumerate(meetings):
    date = m.get("dateString", "Unknown")
    title = m.get("title", "Unknown")[:60] + "..."

    # Highlight April meetings
    april_marker = " 📅 APRIL" if "2025-04" in date else ""
    print(f"{i+1}. {date} - {title}{april_marker}")
