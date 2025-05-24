#!/usr/bin/env python3

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from generate_case_study_optimized import OptimizedCaseStudyGenerator

# Test with FPT domain
generator = OptimizedCaseStudyGenerator("fpt.org.pl")
meetings = generator.fetch_domain_meetings()

print("\n📅 Meeting order in case study:")
for i, meeting in enumerate(meetings):
    date = meeting.get("dateString", "Unknown")
    title = meeting.get("title", "Unknown")
    print(f"{i+1}. {date} - {title}")
