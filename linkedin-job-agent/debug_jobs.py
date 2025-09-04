#!/usr/bin/env python3
"""Debug script to test job card extraction."""

import asyncio
from src.linkedin.browser import LinkedInBrowser
from src.linkedin.scraper import JobScraper
from src.config import Settings

async def debug_job_cards():
    """Debug job card extraction."""
    print("Starting debug job card extraction...")
    print("-" * 50)
    
    settings = Settings()
    settings.headless_mode = False  # Show browser
    browser = LinkedInBrowser(settings)
    
    try:
        # Initialize browser
        await browser.initialize()
        
        # Check if logged in
        logged_in = await browser.check_logged_in()
        if not logged_in:
            print("Not logged in - please login manually")
            return
        
        print("✅ Connected to LinkedIn")
        
        # Navigate to recommended jobs
        print("Navigating to recommended jobs...")
        await browser.search_jobs("", "", False)  # Empty keywords for recommended
        
        # Get first job card only
        print("\nLooking for job cards...")
        scraper = JobScraper(browser.page)
        
        # Try to get just one job
        jobs = await scraper.get_job_listings(max_jobs=1)
        
        if jobs:
            print(f"\n✅ Found {len(jobs)} job(s)")
            job = jobs[0]
            print(f"  Title: {job.job_title}")
            print(f"  Company: {job.company_name}")
            print(f"  Location: {job.location}")
            print(f"  Job ID: {job.job_id}")
        else:
            print("❌ No jobs found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Don't close browser for manual inspection
        print("\nKeeping browser open for inspection...")

if __name__ == "__main__":
    asyncio.run(debug_job_cards())