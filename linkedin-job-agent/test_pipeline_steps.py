#!/usr/bin/env python
"""Step-by-step testing of the LinkedIn job agent pipeline."""

import asyncio
import os
from playwright.async_api import async_playwright

async def test_browser_connection():
    """Test Step 1: Verify browser initialization and Chrome connection."""
    print("\n🧪 TEST STEP 1: Browser Initialization")
    print("=" * 50)
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        print("✅ Connected to Chrome browser")
        
        pages = browser.contexts[0].pages
        print(f"✅ Found {len(pages)} open tabs")
        
        # Find LinkedIn tab
        linkedin_page = None
        for page in pages:
            if "linkedin.com" in page.url:
                linkedin_page = page
                print(f"✅ Found LinkedIn tab: {page.url[:50]}...")
                break
        
        if not linkedin_page:
            print("❌ No LinkedIn tab found")
            return None, None
            
        return browser, linkedin_page
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None, None

async def test_navigation(page):
    """Test Step 2: Verify navigation to LinkedIn recommended jobs page."""
    print("\n🧪 TEST STEP 2: Navigation to Jobs Page")
    print("=" * 50)
    
    try:
        # Navigate to recommended jobs
        url = "https://www.linkedin.com/jobs/collections/recommended/"
        print(f"📍 Navigating to: {url}")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=10000)
        await page.wait_for_timeout(3000)
        
        current_url = page.url
        print(f"✅ Current URL: {current_url[:80]}...")
        
        title = await page.title()
        print(f"✅ Page title: {title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Navigation failed: {e}")
        return False

async def test_job_list_presence(page):
    """Test Step 3: Verify page loads and contains ul.semantic-search-results-list."""
    print("\n🧪 TEST STEP 3: Verify Job List Container")
    print("=" * 50)
    
    try:
        # Check for the main job list container
        selector = "ul.semantic-search-results-list"
        print(f"🔍 Looking for selector: {selector}")
        
        element = await page.query_selector(selector)
        if element:
            print(f"✅ Found job list container!")
            
            # Count job items in the list
            job_items = await page.query_selector_all(f"{selector} > li")
            print(f"✅ Found {len(job_items)} job items in the list")
            
            # Get a sample of HTML to verify structure
            if job_items:
                first_item_html = await job_items[0].inner_html()
                print(f"📄 First job item HTML preview (first 200 chars):")
                print(f"   {first_item_html[:200]}...")
            
            return True
        else:
            print(f"❌ Job list container not found")
            
            # Try alternative selectors to help debug
            alternatives = [
                "div.jobs-search-results",
                "ul.scaffold-layout__list-container",
                "div.jobs-semantic-search-job-details-wrapper"
            ]
            
            print("\n🔍 Checking alternative selectors:")
            for alt in alternatives:
                alt_element = await page.query_selector(alt)
                if alt_element:
                    print(f"  ✓ Found: {alt}")
                else:
                    print(f"  ✗ Not found: {alt}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error checking job list: {e}")
        return False

async def test_job_extraction(page):
    """Test Step 4: Extract and verify job cards from the list."""
    print("\n🧪 TEST STEP 4: Extract Job Cards")
    print("=" * 50)
    
    try:
        # Get all job cards
        job_cards = await page.query_selector_all("ul.semantic-search-results-list > li")
        print(f"📋 Found {len(job_cards)} job cards")
        
        if not job_cards:
            print("❌ No job cards found")
            return []
        
        # Extract basic info from first 3 jobs
        jobs_data = []
        for i, card in enumerate(job_cards[:3]):
            print(f"\n🔍 Analyzing job card #{i+1}:")
            
            # Try to extract job link
            link = await card.query_selector("a[href*='/jobs/view/']")
            if link:
                href = await link.get_attribute("href")
                # Extract job ID from URL
                import re
                match = re.search(r'/jobs/view/(\d+)', href or "")
                job_id = match.group(1) if match else "unknown"
                print(f"  Job ID: {job_id}")
                
                # Try to get job title
                title_text = await link.inner_text()
                print(f"  Title: {title_text[:50]}")
                
                jobs_data.append({
                    "job_id": job_id,
                    "title": title_text,
                    "url": f"https://www.linkedin.com{href}" if href.startswith("/") else href
                })
            
            # Check for Easy Apply
            easy_apply = await card.query_selector("span:has-text('Easy Apply')")
            if easy_apply:
                print(f"  ✅ Has Easy Apply")
        
        print(f"\n✅ Successfully extracted {len(jobs_data)} jobs")
        return jobs_data
        
    except Exception as e:
        print(f"❌ Error extracting jobs: {e}")
        return []

async def test_job_click(page, job_data):
    """Test Step 5: Click on a job and verify job details load."""
    print("\n🧪 TEST STEP 5: Click Job & Load Details")
    print("=" * 50)
    
    if not job_data:
        print("❌ No job data to test")
        return False
    
    try:
        job = job_data[0]
        print(f"🖱️ Clicking on job: {job['title'][:50]}")
        print(f"   Job ID: {job['job_id']}")
        
        # Find and click the job link
        link_selector = f"a[href*='/jobs/view/{job['job_id']}']"
        link = await page.query_selector(link_selector)
        
        if link:
            await link.click()
            await page.wait_for_timeout(3000)
            
            # Check if job details loaded
            details_selector = "div.jobs-semantic-search-job-details-wrapper"
            details = await page.query_selector(details_selector)
            
            if details:
                print("✅ Job details loaded successfully")
                
                # Check for specific job detail elements
                checks = [
                    ("Job title", "h1"),
                    ("Company name", ".job-details-jobs-unified-top-card__company-name"),
                    ("Job description", ".jobs-description__content"),
                    ("Easy Apply button", ".jobs-apply-button")
                ]
                
                for name, selector in checks:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"  ✅ Found: {name}")
                    else:
                        print(f"  ⚠️ Missing: {name}")
                
                return True
            else:
                print("❌ Job details did not load")
                return False
        else:
            print(f"❌ Could not find job link for ID: {job['job_id']}")
            return False
            
    except Exception as e:
        print(f"❌ Error clicking job: {e}")
        return False

async def test_ai_extraction(page):
    """Test Step 6: Extract job details using AI."""
    print("\n🧪 TEST STEP 6: AI Job Details Extraction")
    print("=" * 50)
    
    try:
        # Get the job details HTML
        details_element = await page.query_selector("div.jobs-semantic-search-job-details-wrapper")
        
        if not details_element:
            print("❌ No job details wrapper found")
            return False
        
        html = await details_element.inner_html()
        print(f"📄 Got job details HTML: {len(html)} chars")
        
        # Prepare AI extraction (simplified test)
        import subprocess
        import tempfile
        import json
        
        claude_path = os.path.expanduser("~/claude-eng")
        if not os.path.exists(claude_path):
            print(f"❌ AI tool not found: {claude_path}")
            return False
        
        # Create a simple test prompt
        prompt = f"""Extract the job title and company from this HTML snippet.
Return ONLY JSON: {{"title": "...", "company": "..."}}

HTML (first 5000 chars):
{html[:5000]}"""
        
        # Write to temp file and test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(prompt)
            tmp_path = tmp.name
        
        try:
            print("🤖 Calling AI for extraction...")
            result = subprocess.run(
                f"cat '{tmp_path}' | {claude_path}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                print("✅ AI responded")
                # Try to find JSON in response
                response = result.stdout
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    try:
                        data = json.loads(json_str)
                        print(f"✅ Extracted: {data}")
                        return True
                    except:
                        print(f"⚠️ Could not parse JSON from: {json_str[:100]}")
                else:
                    print(f"⚠️ No JSON found in response: {response[:200]}")
            else:
                print(f"❌ AI extraction failed: {result.stderr}")
        finally:
            os.unlink(tmp_path)
            
        return False
        
    except Exception as e:
        print(f"❌ Error in AI extraction: {e}")
        return False

async def main():
    """Run all test steps sequentially."""
    print("\n" + "=" * 60)
    print("  LINKEDIN JOB AGENT - PIPELINE TEST SUITE")
    print("=" * 60)
    
    # Step 1: Browser connection
    browser, page = await test_browser_connection()
    if not browser:
        print("\n❌ PIPELINE TEST FAILED AT STEP 1")
        return
    
    # Step 2: Navigation
    if not await test_navigation(page):
        print("\n❌ PIPELINE TEST FAILED AT STEP 2")
        await browser.close()
        return
    
    # Step 3: Job list presence
    if not await test_job_list_presence(page):
        print("\n⚠️ WARNING: Job list container not found")
        # Continue anyway to see what's on the page
    
    # Step 4: Job extraction
    jobs_data = await test_job_extraction(page)
    if not jobs_data:
        print("\n⚠️ WARNING: No jobs extracted")
    
    # Step 5: Job click
    if jobs_data:
        if not await test_job_click(page, jobs_data):
            print("\n⚠️ WARNING: Could not click job")
    
    # Step 6: AI extraction
    await test_ai_extraction(page)
    
    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUITE COMPLETED")
    print("=" * 60)
    print("\n📊 Summary:")
    print("  ✅ Browser connection: SUCCESS")
    print("  ✅ Navigation: SUCCESS")
    print(f"  {'✅' if jobs_data else '❌'} Job extraction: {'SUCCESS' if jobs_data else 'FAILED'}")
    
    await browser.close()

if __name__ == "__main__":
    asyncio.run(main())