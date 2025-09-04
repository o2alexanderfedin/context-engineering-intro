#!/usr/bin/env python
"""Analyze ALL items in the job list to understand structure."""

import asyncio
from playwright.async_api import async_playwright

async def analyze_all():
    """Analyze all list items to understand what they contain."""
    print("\n🔍 Analyzing ALL items in LinkedIn job list")
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
    
    # Get ALL scaffold list items
    scaffold_items = await linkedin_page.query_selector_all("li.scaffold-layout__list-item")
    print(f"\n📊 Found {len(scaffold_items)} scaffold list items")
    
    # Analyze each item
    job_count = 0
    other_count = 0
    
    for i, item in enumerate(scaffold_items):
        print(f"\n📦 Item #{i+1}:")
        
        # Check if it has data-job-id
        job_div = await item.query_selector("div[data-job-id]")
        if job_div:
            job_id = await job_div.get_attribute("data-job-id")
            print(f"  ✅ JOB CARD - ID: {job_id}")
            
            # Get job title
            link = await job_div.query_selector("a[href*='/jobs/view/']")
            if link:
                title = await link.inner_text()
                print(f"  Title: {title[:50]}")
            
            job_count += 1
        else:
            # Check what else this could be
            inner_html = await item.inner_html()
            
            # Check for various types of content
            if "Promoted" in inner_html:
                print("  📢 PROMOTED/SPONSORED content")
            elif "People also viewed" in inner_html:
                print("  👥 PEOPLE ALSO VIEWED section")
            elif "job-card" in inner_html:
                print("  📋 Job-related but no data-job-id")
                # Try to extract any job link
                link = await item.query_selector("a[href*='/jobs/view/']")
                if link:
                    href = await link.get_attribute("href")
                    print(f"    Link found: {href[:50]}...")
            elif len(inner_html) < 100:
                print("  ➖ SEPARATOR/SPACER (minimal content)")
            else:
                # Check for any identifiable text
                text_content = await item.inner_text()
                if text_content:
                    preview = text_content[:100].replace('\n', ' ')
                    print(f"  ❓ OTHER: {preview}...")
                else:
                    print("  ❓ UNKNOWN (no text)")
            
            other_count += 1
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"  Job cards with data-job-id: {job_count}")
    print(f"  Other items: {other_count}")
    print(f"  Total scaffold items: {len(scaffold_items)}")
    
    # Also check for job cards outside scaffold
    all_job_cards = await linkedin_page.query_selector_all("div[data-job-id]")
    print(f"\n  Total job cards on page: {len(all_job_cards)}")
    
    await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_all())