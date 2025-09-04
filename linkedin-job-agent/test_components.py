#!/usr/bin/env python3
"""Test individual components of the LinkedIn job agent."""

import asyncio
from pathlib import Path
from src.resume.ai_parser import AIResumeParser
from src.config import Settings, get_settings
from src.linkedin.browser import LinkedInBrowser
from src.linkedin.scraper import JobScraper

async def test_ai_parser():
    """Test AI-based resume parser."""
    print("\n=== Testing AI Resume Parser ===")
    
    # Create a test resume
    test_resume = Path("resume.txt")
    test_resume.write_text("""John Doe
Software Engineer

Skills: Python, JavaScript, TypeScript, React, Node.js, FastAPI, Django
Experience: 10 years building scalable web applications
Education: BS Computer Science""")
    
    try:
        parser = AIResumeParser()
        
        # Test 1: Parse resume
        print("Test 1: Parsing resume...")
        resume_data = parser.parse("resume.txt")
        print(f"  ✓ Resume parsed: {resume_data.get('name', 'Unknown')}")
        if 'skills' in resume_data:
            skills = resume_data['skills'][:5] if isinstance(resume_data['skills'], list) else str(resume_data['skills'])[:50]
            print(f"  ✓ Skills: {skills}")
        
        # Test 2: Get keywords
        print("\nTest 2: Extracting keywords...")
        raw_text = parser._extract_raw_text("resume.txt")
        keywords = parser.get_keywords(raw_text)
        if keywords:
            print(f"  ✓ Keywords: {', '.join(keywords[:5])}")
        
        # Test 3: Match job
        print("\nTest 3: Matching job...")
        job_desc = """
        Senior Software Engineer
        Company: Tech Corp
        Location: San Francisco
        Skills: Python, FastAPI, React
        """
        match_result = parser.match_job(raw_text, job_desc)
        if match_result:
            score = match_result.get('match_score', 0)
            recommendation = match_result.get('recommendation', 'unknown')
            print(f"  ✓ Match score: {score}%")
            print(f"  ✓ Recommendation: {recommendation}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

async def test_browser_connection():
    """Test browser connection and visibility."""
    print("\n=== Testing Browser Connection ===")
    
    settings = get_settings()
    browser = LinkedInBrowser(settings)
    
    try:
        print("Connecting to browser...")
        await browser.initialize()
        print("  ✓ Connected to browser")
        
        # Check if logged in
        is_logged_in = await browser.check_logged_in()
        if is_logged_in:
            print("  ✓ Logged in to LinkedIn")
        else:
            print("  ⚠ Not logged in to LinkedIn")
        
        await asyncio.sleep(2)
        await browser.close()
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

async def test_job_scraping():
    """Test job scraping with page-by-page processing."""
    print("\n=== Testing Job Scraping (Page by Page) ===")
    
    settings = get_settings()
    browser = LinkedInBrowser(settings)
    
    try:
        await browser.initialize()
        
        # Navigate to recommended jobs
        print("Navigating to recommended jobs...")
        await browser.search_jobs("", "San Jose, CA", False)
        
        # Create scraper
        scraper = JobScraper(browser.page)
        
        # Test page-by-page processing
        print("\nTesting page-by-page generator...")
        total_jobs = 0
        page_count = 0
        
        async for page_jobs in scraper.get_job_listings_by_page(max_jobs=10):
            page_count += 1
            if not page_jobs:
                print(f"  Page {page_count}: No jobs found")
                break
            
            print(f"  Page {page_count}: Found {len(page_jobs)} jobs")
            for i, job in enumerate(page_jobs[:3]):  # Show first 3 jobs
                print(f"    {i+1}. {job.job_title} at {job.company_name}")
            
            total_jobs += len(page_jobs)
            
            # Stop after first page for testing
            if page_count >= 1:
                break
        
        print(f"\n  ✓ Total jobs found: {total_jobs}")
        
        await browser.close()
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        await browser.close()
        return False

async def test_scrolling():
    """Test scrolling functionality."""
    print("\n=== Testing Scrolling ===")
    
    settings = get_settings()
    browser = LinkedInBrowser(settings)
    
    try:
        await browser.initialize()
        
        # Navigate to recommended jobs
        print("Navigating to recommended jobs...")
        await browser.search_jobs("", "San Jose, CA", False)
        
        scraper = JobScraper(browser.page)
        
        # Test scrolling
        print("\nTesting scroll to load jobs...")
        initial_count = await scraper._count_job_cards()
        print(f"  Initial job count: {initial_count}")
        
        # Perform scrolling
        await scraper._scroll_to_load_jobs()
        
        final_count = await scraper._count_job_cards()
        print(f"  Final job count: {final_count}")
        
        if final_count > initial_count:
            print(f"  ✓ Scrolling loaded {final_count - initial_count} more jobs")
        else:
            print(f"  ⚠ No additional jobs loaded")
        
        await browser.close()
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        await browser.close()
        return False

async def main():
    """Run all component tests."""
    print("=" * 60)
    print("LinkedIn Job Agent - Component Tests")
    print("=" * 60)
    
    # Update todo
    print("\n📋 Test Plan:")
    print("1. AI Resume Parser")
    print("2. Browser Connection")
    print("3. Job Scraping (Page by Page)")
    print("4. Scrolling Functionality")
    
    results = []
    
    # Test AI parser
    results.append(("AI Parser", await test_ai_parser()))
    
    # Test browser
    results.append(("Browser", await test_browser_connection()))
    
    # Test scraping
    results.append(("Scraping", await test_job_scraping()))
    
    # Test scrolling
    results.append(("Scrolling", await test_scrolling()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)