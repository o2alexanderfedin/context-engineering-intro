#!/usr/bin/env python
"""Complete pipeline test for LinkedIn Job Agent."""

import asyncio
from src.resume.ai_parser import AIResumeParser
from src.linkedin.browser import LinkedInBrowser
from src.linkedin.scraper import JobScraper
from src.config import get_settings

async def test_complete_pipeline():
    """Test the complete pipeline step by step."""
    print("=" * 60)
    print("  COMPLETE PIPELINE TEST")
    print("=" * 60)
    
    # Step 1: Test AI Resume Parser
    print("\n✅ STEP 1: AI Resume Parsing")
    print("-" * 40)
    parser = AIResumeParser()
    
    # Test parse
    resume_data = parser.parse("resume.txt")
    if resume_data:
        print(f"  Name extracted: {resume_data.get('name', 'Unknown')}")
        print(f"  Email: {resume_data.get('email', 'Not found')}")
        if 'skills' in resume_data and resume_data['skills']:
            print(f"  Skills found: {len(resume_data['skills']) if isinstance(resume_data['skills'], list) else 'Yes'}")
    else:
        print("  Parse failed - AI did not respond")
    
    # Test keywords
    resume_text = parser._extract_raw_text("resume.txt")
    keywords = parser.get_keywords(resume_text)
    print(f"  Keywords extracted: {len(keywords)}")
    
    # Test job matching
    test_job = "Senior Python Developer - Remote - Python, Django, AWS"
    match = parser.match_job(resume_text, test_job)
    print(f"  Job matching works: {'match_score' in match}")
    
    # Step 2: Test Browser Connection
    print("\n✅ STEP 2: Browser Connection")
    print("-" * 40)
    settings = get_settings()
    browser = LinkedInBrowser(settings)
    
    try:
        await browser.initialize()
        print("  Browser connected successfully")
        
        is_logged_in = await browser.check_logged_in()
        print(f"  LinkedIn login status: {'Logged in' if is_logged_in else 'Not logged in'}")
        
        # Step 3: Test Job Scraping
        print("\n✅ STEP 3: Job Scraping with Scrolling")
        print("-" * 40)
        
        # Navigate to jobs
        await browser.search_jobs("", "", False)  # Use recommended
        
        # Create scraper
        scraper = JobScraper(browser.page)
        
        # Test with scrolling
        jobs = await scraper.get_job_listings(max_jobs=10)
        print(f"  Jobs extracted: {len(jobs)}")
        
        if jobs:
            print(f"  First job: {jobs[0].job_title} at {jobs[0].company_name}")
            print(f"  Has scrolling: {len(jobs) > 9}")
        
        # Step 4: Test AI Job Matching
        print("\n✅ STEP 4: AI Job Matching")
        print("-" * 40)
        
        if jobs:
            test_job_desc = f"""
Job Title: {jobs[0].job_title}
Company: {jobs[0].company_name}
Location: {jobs[0].location}
"""
            match_result = parser.match_job(resume_text, test_job_desc)
            if match_result and isinstance(match_result, dict):
                print(f"  Match score: {match_result.get('match_score', 'N/A')}")
                print(f"  Recommendation: {match_result.get('recommendation', 'N/A')}")
            else:
                print("  Match failed")
        
        print("\n✅ ALL TESTS COMPLETED")
        
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())