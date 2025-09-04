#!/usr/bin/env python
"""Inspect the actual job structure on LinkedIn to find all jobs."""

import asyncio
from playwright.async_api import async_playwright

async def inspect_structure():
    """Inspect job structure on the page."""
    print("\n🔍 Inspecting LinkedIn job page structure")
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
    await linkedin_page.wait_for_timeout(5000)
    
    print("\n📊 Looking for different job card structures:")
    
    # Method 1: data-job-id attribute
    job_cards_1 = await linkedin_page.query_selector_all("div[data-job-id]")
    print(f"\n1. div[data-job-id]: {len(job_cards_1)} jobs")
    
    # Method 2: Look for scaffold-layout list items
    scaffold_items = await linkedin_page.query_selector_all("li.scaffold-layout__list-item")
    print(f"\n2. li.scaffold-layout__list-item: {len(scaffold_items)} items")
    
    # Method 3: Look for job card containers
    job_containers = await linkedin_page.query_selector_all("div.job-card-container")
    print(f"\n3. div.job-card-container: {len(job_containers)} containers")
    
    # Method 4: Look for all list items in scaffold
    scaffold_list = await linkedin_page.query_selector("ul.scaffold-layout__list-container")
    if scaffold_list:
        list_items = await scaffold_list.query_selector_all("li")
        print(f"\n4. ul.scaffold-layout__list-container > li: {len(list_items)} items")
    
    # Method 5: Look for jobs-search-results__list
    jobs_list = await linkedin_page.query_selector("ul.jobs-search-results__list")
    if jobs_list:
        jobs_items = await jobs_list.query_selector_all("li")
        print(f"\n5. ul.jobs-search-results__list > li: {len(jobs_items)} items")
    else:
        print("\n5. ul.jobs-search-results__list: Not found")
    
    # Method 6: Look by aria-label
    job_links = await linkedin_page.query_selector_all("a[aria-label*='job']")
    print(f"\n6. Links with 'job' in aria-label: {len(job_links)} links")
    
    # Method 7: Check the main container structure
    print("\n📦 Checking main container structure:")
    
    # Look for the main jobs container
    main_container = await linkedin_page.query_selector("div.jobs-search-two-pane__wrapper")
    if main_container:
        print("  ✅ Found jobs-search-two-pane__wrapper")
        
        # Look for left pane (job list)
        left_pane = await main_container.query_selector("div.scaffold-layout__list-container")
        if left_pane:
            print("  ✅ Found scaffold-layout__list-container")
            
            # Try to get all children
            all_children = await linkedin_page.evaluate('''() => {
                const container = document.querySelector('div.scaffold-layout__list-container');
                if (container) {
                    const children = container.querySelectorAll('*');
                    return {
                        totalChildren: children.length,
                        directChildren: container.children.length,
                        ulElements: container.querySelectorAll('ul').length,
                        liElements: container.querySelectorAll('li').length,
                        divWithDataJobId: container.querySelectorAll('div[data-job-id]').length
                    };
                }
                return null;
            }''')
            
            if all_children:
                print(f"    Total children: {all_children['totalChildren']}")
                print(f"    Direct children: {all_children['directChildren']}")
                print(f"    UL elements: {all_children['ulElements']}")
                print(f"    LI elements: {all_children['liElements']}")
                print(f"    DIVs with data-job-id: {all_children['divWithDataJobId']}")
    
    # Method 8: Use JavaScript to find all clickable job elements
    print("\n🔍 Using JavaScript to find all job elements:")
    
    job_count = await linkedin_page.evaluate('''() => {
        // Find all elements that look like job cards
        const results = {};
        
        // Method 1: Count all links to /jobs/view/
        const jobLinks = document.querySelectorAll('a[href*="/jobs/view/"]');
        results.jobLinks = jobLinks.length;
        
        // Method 2: Count unique job IDs from links
        const jobIds = new Set();
        jobLinks.forEach(link => {
            const match = link.href.match(/\/jobs\/view\/(\d+)/);
            if (match) jobIds.add(match[1]);
        });
        results.uniqueJobIds = jobIds.size;
        
        // Method 3: Count all elements with job in class name
        const jobElements = document.querySelectorAll('[class*="job-card"]');
        results.jobCardElements = jobElements.length;
        
        // Method 4: Get the actual list container
        const listContainer = document.querySelector('.scaffold-layout__list-container');
        if (listContainer) {
            results.listItems = listContainer.querySelectorAll('li').length;
            results.listDivs = listContainer.querySelectorAll('div[data-job-id]').length;
        }
        
        // Method 5: Find pagination info
        const pagination = document.querySelector('.jobs-search-pagination');
        if (pagination) {
            results.paginationText = pagination.innerText;
        }
        
        return results;
    }''')
    
    print(f"  Job links found: {job_count.get('jobLinks', 0)}")
    print(f"  Unique job IDs: {job_count.get('uniqueJobIds', 0)}")
    print(f"  Job card elements: {job_count.get('jobCardElements', 0)}")
    print(f"  List items: {job_count.get('listItems', 0)}")
    print(f"  Divs with data-job-id: {job_count.get('listDivs', 0)}")
    if job_count.get('paginationText'):
        print(f"  Pagination: {job_count.get('paginationText')}")
    
    # Try to scroll and load more
    print("\n📜 Attempting to load more jobs by scrolling:")
    
    # Find the scrollable container
    scroll_result = await linkedin_page.evaluate('''async () => {
        const container = document.querySelector('.jobs-search-results-list');
        if (container) {
            // Scroll to bottom
            container.scrollTop = container.scrollHeight;
            
            // Wait a bit
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Count again
            const jobCards = document.querySelectorAll('div[data-job-id]');
            return {
                found: true,
                jobCount: jobCards.length,
                containerHeight: container.scrollHeight
            };
        }
        return { found: false };
    }''')
    
    if scroll_result['found']:
        print(f"  ✅ Scrolled container, now have {scroll_result['jobCount']} jobs")
        print(f"  Container height: {scroll_result['containerHeight']}px")
    else:
        print("  ❌ Could not find scrollable container")
    
    await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_structure())