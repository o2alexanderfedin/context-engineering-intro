#!/usr/bin/env python
"""Debug job matching to see why no jobs are passing criteria."""

from src.resume.ai_parser import AIResumeParser
from src.config import get_settings

def debug_matching():
    """Debug the job matching process."""
    parser = AIResumeParser()
    settings = get_settings()
    
    print("🔍 Debugging Job Matching")
    print("=" * 50)
    
    # Parse resume
    print("\n1. Parsing resume...")
    resume_text = parser._extract_raw_text("resume.txt")
    
    # Sample job from actual LinkedIn
    sample_job = """
Job Title: Principal Software Engineer (Cloud Security)
Company: Palo Alto Networks  
Location: Remote
Work Arrangement: remote
Easy Apply: yes
URL: https://linkedin.com/jobs/123
"""
    
    print("\n2. Testing job match...")
    match_result = parser.match_job(resume_text, sample_job)
    
    print(f"\nMatch result:")
    print(f"  Score: {match_result.get('match_score', 'N/A')}")
    print(f"  Recommendation: {match_result.get('recommendation', 'N/A')}")
    
    # Check criteria
    score = match_result.get('match_score', 0) / 100.0
    min_score = settings.min_match_score
    
    print(f"\n3. Checking criteria:")
    print(f"  Job score: {score:.2f}")
    print(f"  Min required score: {min_score}")
    print(f"  Recommendation: {match_result.get('recommendation')}")
    
    # Check if would pass
    would_pass = match_result.get('recommendation') in ['yes', 'maybe'] or score >= min_score
    print(f"\n  Would pass criteria? {would_pass}")
    
    if not would_pass:
        print(f"\n  Reason: Score {score:.2f} < {min_score} and recommendation is '{match_result.get('recommendation')}'")

if __name__ == "__main__":
    debug_matching()