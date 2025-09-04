#!/usr/bin/env python
"""Count all jobs on the LinkedIn page, including those that need scrolling."""

import asyncio
from playwright.async_api import async_playwright

async def count_jobs():
    """Count all job cards on the page."""
    print("\n🔍 Counting ALL jobs on LinkedIn page")
    print("=" * 50)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
    
    # Find LinkedIn tab
    linkedin_page = None
    for page in browser.contexts[0].pages:
        if "linkedin.com" in page.url:
            linkedin_page = page
            print(f"✅ Found LinkedIn tab: {page.url[:50]}...")
            break
    
    if not linkedin_page:
        print("❌ No LinkedIn tab found")
        await browser.close()
        return
    
    # Navigate to recommended jobs
    url = "https://www.linkedin.com/jobs/collections/recommended/"
    print(f"📍 Navigating to: {url}")
    await linkedin_page.goto(url, wait_until="domcontentloaded", timeout=10000)
    await linkedin_page.wait_for_timeout(3000)
    
    print("\n📊 Initial count:")
    # Count visible jobs
    job_cards = await linkedin_page.query_selector_all("div[data-job-id]")
    print(f"  Found {len(job_cards)} job cards with data-job-id")
    
    # Try different selectors
    links = await linkedin_page.query_selector_all("a[href*='/jobs/view/']")
    print(f"  Found {len(links)} job links")
    
    # Check for job list container
    job_list = await linkedin_page.query_selector("div.jobs-search-results-list")
    if job_list:
        print("  ✅ Found jobs-search-results-list container")
    
    # Try scrolling to load more jobs
    print("\n📜 Scrolling to load more jobs...")
    
    # Get the scrollable container
    scrollable_selector = "div.jobs-search-results-list"
    scrollable = await linkedin_page.query_selector(scrollable_selector)
    
    if scrollable:
        for i in range(5):  # Try scrolling 5 times
            # Scroll the container
            await linkedin_page.evaluate('''(selector) => {
                const element = document.querySelector(selector);
                if (element) {
                    element.scrollTop = element.scrollHeight;
                }
            }''', scrollable_selector)
            
            await linkedin_page.wait_for_timeout(2000)  # Wait for new jobs to load
            
            # Count again
            new_job_cards = await linkedin_page.query_selector_all("div[data-job-id]")
            print(f"  After scroll {i+1}: {len(new_job_cards)} jobs")
            
            if len(new_job_cards) == len(job_cards):
                print("    No new jobs loaded")
                break
            job_cards = new_job_cards
    else:
        print("  ❌ Could not find scrollable container")
        
        # Try scrolling the main window
        print("\n📜 Trying to scroll main window...")
        for i in range(3):
            await linkedin_page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await linkedin_page.wait_for_timeout(2000)
            
            new_job_cards = await linkedin_page.query_selector_all("div[data-job-id]")
            print(f"  After scroll {i+1}: {len(new_job_cards)} jobs")
            
            if len(new_job_cards) == len(job_cards):
                break
            job_cards = new_job_cards
    
    # Final count with all selectors
    print("\n📊 Final count:")
    final_job_cards = await linkedin_page.query_selector_all("div[data-job-id]")
    print(f"  Total job cards found: {len(final_job_cards)}")
    
    # Get job IDs to verify uniqueness
    job_ids = set()
    for card in final_job_cards:
        job_id = await card.get_attribute("data-job-id")
        if job_id:
            job_ids.add(job_id)
    
    print(f"  Unique job IDs: {len(job_ids)}")
    
    # Sample some job IDs
    if job_ids:
        sample_ids = list(job_ids)[:5]
        print(f"  Sample IDs: {sample_ids}")
    
    await browser.close()

if __name__ == "__main__":
    asyncio.run(count_jobs())