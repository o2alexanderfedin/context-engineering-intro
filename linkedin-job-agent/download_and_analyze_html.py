#!/usr/bin/env python
"""Download and analyze HTML from LinkedIn jobs page to find correct selectors."""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def download_html():
    """Download HTML from LinkedIn jobs page."""
    print("\n🔍 Downloading LinkedIn HTML for analysis")
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
    await linkedin_page.wait_for_timeout(5000)  # Wait for dynamic content
    
    # Get the full HTML
    html = await linkedin_page.content()
    print(f"✅ Downloaded HTML: {len(html)} chars")
    
    # Save to file
    with open("linkedin_jobs_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Saved to linkedin_jobs_page.html")
    
    await browser.close()
    return html

def analyze_html(html):
    """Analyze HTML to find job-related selectors."""
    print("\n📊 Analyzing HTML structure")
    print("=" * 50)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for job list containers
    print("\n🔍 Searching for job list containers...")
    
    # Find ul with class containing 'semantic-search-results-list'
    job_lists = soup.find_all('ul', class_=re.compile(r'semantic-search-results-list'))
    if job_lists:
        for ul in job_lists:
            classes = ul.get('class', [])
            print(f"  ✅ Found <ul> with classes: {' '.join(classes)}")
            
            # Count list items
            li_items = ul.find_all('li', recursive=False)
            print(f"     Contains {len(li_items)} <li> items")
            
            # Check first item structure
            if li_items:
                first_li = li_items[0]
                # Look for job links
                job_links = first_li.find_all('a', href=re.compile(r'/jobs/view/\d+'))
                if job_links:
                    print(f"     First item has {len(job_links)} job link(s)")
                    for link in job_links[:1]:
                        print(f"       Example href: {link.get('href', '')[:50]}...")
    else:
        print("  ❌ No <ul> with 'semantic-search-results-list' class found")
        
        # Try alternative selectors
        print("\n  Looking for alternative job list structures...")
        
        # Check for divs with job-related classes
        job_divs = soup.find_all('div', class_=re.compile(r'jobs-search-results'))
        if job_divs:
            for div in job_divs:
                print(f"  Found <div> with class: {' '.join(div.get('class', []))}")
    
    # Look for job detail containers
    print("\n🔍 Searching for job detail containers...")
    job_details = soup.find_all('div', class_=re.compile(r'jobs-semantic-search-job-details-wrapper'))
    if job_details:
        for div in job_details:
            classes = div.get('class', [])
            print(f"  ✅ Found job details <div> with classes: {' '.join(classes)}")
    else:
        print("  ❌ No job details wrapper found")
    
    # Look for job cards by href pattern
    print("\n🔍 Searching for job cards by href pattern...")
    job_links = soup.find_all('a', href=re.compile(r'/jobs/view/\d+'))
    if job_links:
        print(f"  ✅ Found {len(job_links)} job links")
        
        # Analyze parent structure of first few links
        for i, link in enumerate(job_links[:3]):
            print(f"\n  Job link #{i+1}:")
            print(f"    href: {link.get('href', '')[:50]}...")
            
            # Check parent elements
            parent = link.parent
            depth = 0
            while parent and depth < 5:
                if parent.name:
                    classes = parent.get('class', [])
                    if classes:
                        print(f"    {'  ' * depth}Parent <{parent.name}> class: {' '.join(classes[:2])}...")
                depth += 1
                parent = parent.parent
    
    # Look for Easy Apply buttons
    print("\n🔍 Searching for Easy Apply buttons...")
    easy_apply = soup.find_all(string=re.compile(r'Easy Apply', re.IGNORECASE))
    if easy_apply:
        print(f"  ✅ Found {len(easy_apply)} 'Easy Apply' text instances")
    
    # Look for job title elements
    print("\n🔍 Searching for job title patterns...")
    h1_titles = soup.find_all('h1')
    h2_titles = soup.find_all('h2')
    h3_titles = soup.find_all('h3')
    
    print(f"  Found {len(h1_titles)} <h1>, {len(h2_titles)} <h2>, {len(h3_titles)} <h3> elements")
    
    # Check for job-related attributes
    print("\n🔍 Searching for data attributes...")
    elements_with_job_id = soup.find_all(attrs={'data-job-id': True})
    if elements_with_job_id:
        print(f"  ✅ Found {len(elements_with_job_id)} elements with data-job-id")
        for elem in elements_with_job_id[:2]:
            print(f"    <{elem.name}> data-job-id='{elem.get('data-job-id')}'")
    
    return {
        'has_semantic_list': bool(job_lists),
        'job_link_count': len(job_links),
        'has_job_details': bool(job_details),
        'has_easy_apply': bool(easy_apply)
    }

def extract_css_selectors(html):
    """Extract working CSS selectors from the HTML."""
    print("\n🎯 Extracting CSS selectors for automation")
    print("=" * 50)
    
    soup = BeautifulSoup(html, 'html.parser')
    selectors = {}
    
    # Find the job list UL
    job_list_ul = soup.find('ul', class_=re.compile(r'semantic-search-results-list'))
    if job_list_ul:
        classes = job_list_ul.get('class', [])
        # Use attribute selector for partial class match
        selectors['job_list'] = 'ul[class*="semantic-search-results-list"]'
        print(f"✅ Job list selector: {selectors['job_list']}")
        
        # Get job item selector
        selectors['job_items'] = 'ul[class*="semantic-search-results-list"] > li'
        print(f"✅ Job items selector: {selectors['job_items']}")
    
    # Find job detail wrapper
    job_detail_div = soup.find('div', class_=re.compile(r'jobs-semantic-search-job-details-wrapper'))
    if job_detail_div:
        selectors['job_details'] = 'div[class*="jobs-semantic-search-job-details-wrapper"]'
        print(f"✅ Job details selector: {selectors['job_details']}")
    
    # Job link selector
    selectors['job_links'] = 'a[href*="/jobs/view/"]'
    print(f"✅ Job links selector: {selectors['job_links']}")
    
    # Easy Apply selector options
    selectors['easy_apply'] = [
        'span:has-text("Easy Apply")',
        'button[aria-label*="Easy Apply"]',
        'button:has-text("Easy Apply")',
        '.jobs-apply-button'
    ]
    print(f"✅ Easy Apply selectors: {selectors['easy_apply']}")
    
    return selectors

async def main():
    """Main function."""
    # Download HTML
    html = await download_html()
    
    if html:
        # Analyze structure
        analysis = analyze_html(html)
        
        # Extract selectors
        selectors = extract_css_selectors(html)
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 SUMMARY")
        print("=" * 50)
        print(f"✅ HTML downloaded: {len(html)} chars")
        print(f"✅ Has semantic list: {analysis['has_semantic_list']}")
        print(f"✅ Job links found: {analysis['job_link_count']}")
        print(f"✅ Has job details: {analysis['has_job_details']}")
        print(f"✅ Has Easy Apply: {analysis['has_easy_apply']}")
        
        print("\n🎯 RECOMMENDED SELECTORS:")
        for key, value in selectors.items():
            if isinstance(value, list):
                print(f"  {key}:")
                for v in value:
                    print(f"    - {v}")
            else:
                print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())