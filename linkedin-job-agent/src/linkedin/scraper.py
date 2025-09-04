"""Job listing scraper for LinkedIn using AI extraction."""

import json
import os
import subprocess
import tempfile
from datetime import datetime

from playwright.async_api import Page

from ..database.models import JobListing


class JobScraper:
    """Scrape job listings from LinkedIn using AI."""

    def __init__(self, page: Page):
        """Initialize scraper with page."""
        self.page = page
        self.claude_path = os.path.expanduser("~/claude-eng")

    async def get_job_listings(self, max_jobs: int = 50) -> list[JobListing]:
        """Get job listings from search results - backward compatibility method."""
        jobs = []
        async for page_jobs in self.get_job_listings_by_page(max_jobs):
            jobs.extend(page_jobs)
            if len(jobs) >= max_jobs:
                break
        return jobs[:max_jobs]
    
    async def get_job_listings_by_page(self, max_jobs: int = 50):
        """Generator that yields job listings page by page for immediate processing."""
        page_num = 1
        max_pages = 5  # Limit to 5 pages to avoid infinite loops
        total_collected = 0
        
        while total_collected < max_jobs and page_num <= max_pages:
            print(f"\n📄 Page {page_num}:")
            
            # Get entire page HTML and let AI extract jobs
            page_jobs = await self._extract_jobs_from_page()
            
            if not page_jobs:
                print("  No jobs found on this page")
                break
                
            # Yield only the needed amount
            jobs_to_yield = page_jobs[:max_jobs - total_collected]
            yield jobs_to_yield
            
            total_collected += len(jobs_to_yield)
            print(f"  Page {page_num} extracted: {len(jobs_to_yield)} jobs")
            
            if total_collected >= max_jobs:
                print(f"  Reached job limit ({max_jobs})")
                break

            # Go to next page
            has_next = await self._go_to_next_page()
            if not has_next:
                print("  No more pages available")
                break

            page_num += 1
            # Wait between pages for content to load
            await self.page.wait_for_timeout(3000)

    async def _extract_jobs_from_page(self) -> list[JobListing]:
        """Extract all jobs from current page using AI."""
        jobs = []
        
        # Wait for initial page to load
        await self.page.wait_for_timeout(3000)
        
        # Scroll to load all jobs on the page
        print("📜 Scrolling to load all jobs...")
        await self._scroll_job_list()
        
        # Get the entire page HTML after scrolling
        try:
            page_html = await self.page.content()
            print(f"📄 Got page HTML after scrolling: {len(page_html)} chars")
        except Exception as e:
            print(f"❌ Failed to get page HTML: {e}")
            return jobs

        if not os.path.exists(self.claude_path):
            print(f"❌ AI tool not found: {self.claude_path}")
            return jobs
        
        # Try to extract specific job-related sections to reduce HTML size
        if len(page_html) > 400000:
            print(f"⚠️ HTML too large ({len(page_html)} chars), extracting job sections...")
            
            # Try to get job details and list containers
            try:
                # First try to get the job list container
                job_container_selectors = [
                    "div[data-job-id]",  # Job cards with data-job-id attribute
                    "div.job-card-container",  # Job card containers
                    "div.jobs-semantic-search-job-details-wrapper",  # Job details wrapper
                    "div.jobs-search-results",
                    "div.jobs-search-results-list", 
                    "main",
                    "div[role='main']"
                ]
                
                for selector in job_container_selectors:
                    try:
                        # For data-job-id selector, get ALL job cards
                        if selector == "div[data-job-id]":
                            elements = await self.page.query_selector_all(selector)
                            if elements and len(elements) > 0:
                                print(f"  Found {len(elements)} job cards")
                                combined_html = ""
                                for elem in elements:
                                    elem_html = await elem.inner_html()
                                    job_id = await elem.get_attribute("data-job-id")
                                    combined_html += f'<div data-job-id="{job_id}" class="job-card">{elem_html}</div>\n'
                                
                                if len(combined_html) > 1000:
                                    page_html = f"<div class='extracted-jobs'>{combined_html}</div>"
                                    print(f"✅ Extracted {len(elements)} job containers: {len(page_html)} chars using {selector}")
                                    break
                        else:
                            element = await self.page.query_selector(selector)
                            if element:
                                container_html = await element.inner_html()
                                if container_html and len(container_html) > 1000:
                                    page_html = f"<div class='extracted-jobs'>{container_html}</div>"
                                    print(f"✅ Extracted job container: {len(page_html)} chars using {selector}")
                                    break
                    except:
                        continue
                        
                # If still too large, truncate but keep structure
                if len(page_html) > 400000:
                    print(f"  Still too large, truncating to 400KB...")
                    page_html = page_html[:400000]
                    
            except Exception as e:
                print(f"  Failed to extract job container: {e}")
                # Truncate the full HTML
                page_html = page_html[:400000]

        # Create prompt for AI to extract ALL job listings
        prompt = f"""Extract ALL job listings from this LinkedIn jobs page HTML.

Look for job cards in these structures:
- <div> elements with data-job-id attribute (e.g., data-job-id="4210108588")
- <div> elements with class "job-card-container"
- Links with href="/jobs/view/[job_id]"
- div.jobs-semantic-search-job-details-wrapper (for selected job details)
- Easy Apply buttons with class "jobs-apply-button" or data-job-id attributes

For EACH job listing found (look for ALL div[data-job-id] elements), extract:
- job_id: LinkedIn job ID (from data-job-id attribute or URLs like /jobs/view/4292436628)
- title: Job title (often in links or span elements within the job card)
- company: Company name (look for company-name classes or text after the title)
- location: Job location (including Remote/Hybrid indicators)
- salary: Salary range if shown (e.g., "$45/hr - $50/hr")
- posted_date: When posted (e.g., "6 days ago")
- job_url: Full LinkedIn URL to the job (/jobs/view/[job_id])
- easy_apply: true if Easy Apply text or button exists for this job
- applicants: Number of applicants if shown

Return ONLY a JSON array of job objects.
Example format:
[
  {{
    "job_id": "4292436628",
    "title": "Application Developer",
    "company": "netPolarity, Inc.",
    "location": "United States (Remote)",
    "salary": "$45/hr - $50/hr",
    "posted_date": "6 days ago",
    "job_url": "https://linkedin.com/jobs/view/4292436628",
    "easy_apply": true,
    "applicants": "Over 100 applicants"
  }}
]

HTML:
{page_html}"""

        # Write prompt to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(prompt)
            tmp_path = tmp_file.name

        try:
            print("🤖 Asking AI to extract all job listings from page...")
            
            # Run AI extraction with temp file
            result = subprocess.run(
                f"cat '{tmp_path}' | {self.claude_path}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0 and result.stdout:
                try:
                    # Find JSON array in response
                    response = result.stdout
                    json_start = response.find('[')
                    json_end = response.rfind(']') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = response[json_start:json_end]
                        job_data_list = json.loads(json_str)
                        
                        print(f"✅ AI extracted {len(job_data_list)} jobs")
                        
                        # Convert each job data to JobListing
                        for job_data in job_data_list:
                            try:
                                # Determine work arrangement
                                location = job_data.get('location', '')
                                work_arrangement = job_data.get('work_arrangement', 'onsite')
                                if not work_arrangement or work_arrangement == 'onsite':
                                    if 'remote' in location.lower():
                                        work_arrangement = 'remote'
                                    elif 'hybrid' in location.lower():
                                        work_arrangement = 'hybrid'
                                
                                # Parse posting date
                                posting_date = None
                                if job_data.get('posted_date'):
                                    try:
                                        posting_date = datetime.fromisoformat(job_data['posted_date'])
                                    except:
                                        pass
                                
                                job = JobListing(
                                    job_id=str(job_data.get('job_id', '')),
                                    job_title=job_data.get('title', 'Unknown'),
                                    company_name=job_data.get('company', 'Unknown'),
                                    location=location,
                                    work_arrangement=work_arrangement,
                                    posting_date=posting_date,
                                    job_url=job_data.get('job_url', ''),
                                    easy_apply=job_data.get('easy_apply', False),
                                )
                                
                                if job.job_id:  # Only add if we have a valid ID
                                    jobs.append(job)
                                    print(f"  📌 {job.job_title} at {job.company_name}")
                                    
                            except Exception as e:
                                print(f"  ⚠️ Failed to parse job: {e}")
                                continue
                    else:
                        print("❌ No JSON array found in AI response")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse AI response as JSON: {e}")
                    print(f"Response preview: {result.stdout[:500]}")
            else:
                print(f"❌ AI extraction failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("❌ AI extraction timed out")
        except Exception as e:
            print(f"❌ AI extraction error: {e}")
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return jobs

    async def _scroll_job_list(self):
        """Scroll the job list to load all jobs."""
        try:
            # First, find the scrollable container
            selectors_to_try = [
                "div.jobs-search-results-list",
                "div.scaffold-layout__list-container", 
                "div.jobs-search-results",
                "main"
            ]
            
            scrollable_element = None
            for selector in selectors_to_try:
                element = await self.page.query_selector(selector)
                if element:
                    scrollable_element = selector
                    print(f"  Found scrollable container: {selector}")
                    break
            
            if not scrollable_element:
                print("  No scrollable container found, scrolling main window")
                scrollable_element = "window"
            
            # Count initial jobs
            initial_jobs = await self.page.query_selector_all("div[data-job-id]")
            print(f"  Initial job count: {len(initial_jobs)}")
            
            # Scroll multiple times to load all jobs
            last_count = len(initial_jobs)
            no_new_jobs_count = 0
            
            # LinkedIn typically has 25 jobs per page, keep scrolling until we get them all
            for i in range(15):  # Max 15 scrolls to load all jobs
                # Scroll the container or window
                if scrollable_element == "window":
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                else:
                    await self.page.evaluate(f'''
                        const element = document.querySelector('{scrollable_element}');
                        if (element) {{
                            element.scrollTop = element.scrollHeight;
                        }}
                    ''')
                
                # Wait longer for new content to load (LinkedIn can be slow)
                await self.page.wait_for_timeout(3000)
                
                # Count jobs again
                current_jobs = await self.page.query_selector_all("div[data-job-id]")
                current_count = len(current_jobs)
                
                print(f"  After scroll {i+1}: {current_count} jobs")
                
                # Check if new jobs were loaded
                if current_count == last_count:
                    no_new_jobs_count += 1
                    # Need more consecutive no-new-jobs before stopping (LinkedIn loads slowly)
                    if no_new_jobs_count >= 3 and current_count >= 20:
                        # If we have at least 20 jobs and no new ones for 3 scrolls, stop
                        print(f"  No new jobs after {no_new_jobs_count} scrolls with {current_count} jobs, stopping")
                        break
                    elif no_new_jobs_count >= 5:
                        # Absolute stop after 5 consecutive scrolls with no new jobs
                        print(f"  No new jobs after {no_new_jobs_count} scrolls, stopping")
                        break
                else:
                    no_new_jobs_count = 0
                    last_count = current_count
                
                # If we have 25 jobs (typical LinkedIn page size), we can stop
                if current_count >= 25:
                    print(f"  Reached typical page size ({current_count} jobs), stopping")
                    break
            
            # Final count
            final_jobs = await self.page.query_selector_all("div[data-job-id]")
            print(f"  Final job count after scrolling: {len(final_jobs)}")
            
        except Exception as e:
            print(f"  Error during scrolling: {e}")

    async def _go_to_next_page(self) -> bool:
        """Navigate to next page of results."""
        try:
            print("  Looking for pagination controls...")
            
            # Method 1: Look for "Next" button
            next_button = await self.page.query_selector("button[aria-label*='Page 2']")
            if not next_button:
                next_button = await self.page.query_selector("button[aria-label*='next']")
            if not next_button:
                next_button = await self.page.query_selector("button:has-text('Next')")
            
            # Method 2: Look for pagination numbers
            if not next_button:
                # Look for page number buttons (2, 3, etc.)
                pagination = await self.page.query_selector("div.jobs-search-pagination")
                if pagination:
                    # Try to click on page 2, 3, etc.
                    page_buttons = await pagination.query_selector_all("button")
                    for button in page_buttons:
                        text = await button.inner_text()
                        if text.isdigit() and int(text) > 1:
                            next_button = button
                            print(f"  Found page {text} button")
                            break

            if next_button:
                is_disabled = await next_button.get_attribute("disabled")
                if not is_disabled:
                    print("  Clicking next page...")
                    await next_button.click()
                    # Wait for new jobs to load
                    await self.page.wait_for_timeout(3000)
                    
                    # Verify page changed by checking for new job IDs
                    await self.page.wait_for_selector("div[data-job-id]", timeout=5000)
                    return True
                else:
                    print("  Next button is disabled")

            print("  No next page button found")
            return False

        except Exception as e:
            print(f"  Failed to navigate to next page: {e}")
            return False

    async def get_job_details(self, job_listing: JobListing) -> dict[str, any]:
        """Get detailed information for a specific job using AI."""
        try:
            # Navigate to job page
            print(f"\n🔍 Getting details for: {job_listing.job_title}")
            await self.page.goto(job_listing.job_url, wait_until="domcontentloaded", timeout=10000)
            await self.page.wait_for_timeout(3000)

            # Get entire job page HTML
            job_page_html = await self.page.content()
            print(f"  📄 Job page HTML: {len(job_page_html)} chars")

            if not os.path.exists(self.claude_path):
                print(f"❌ AI tool not found: {self.claude_path}")
                return {}

            # Get resume data for context
            resume_file = "resume.txt"
            resume_content = ""
            if os.path.exists(resume_file):
                with open(resume_file, 'r') as f:
                    resume_content = f.read()

            # Create prompt for AI to extract job details AND decide suitability
            prompt = f"""Analyze this LinkedIn job posting page and extract ALL details.

IMPORTANT: Also determine if this job is suitable based on the resume provided.

Extract the following information:
1. Full job description (ALL of it, including responsibilities, requirements, benefits)
2. Required skills (ALL mentioned skills)
3. Salary range (if mentioned)
4. Employment type (full-time, part-time, contract, etc.)
5. Seniority level (entry, mid, senior, lead, etc.)
6. Industry
7. Benefits mentioned
8. Application deadline (if any)
9. Number of applicants (if shown)
10. Posted date
11. Any other relevant information

MOST IMPORTANTLY, answer:
- is_suitable: true/false - Would this job be a good match for the resume?
- suitability_score: 0-100 - How well does this match (0=terrible, 100=perfect)?
- suitability_reasons: List of reasons why it's suitable or not
- missing_skills: Skills required that are not in the resume
- matching_skills: Skills that match between job and resume

RESUME:
{resume_content}

JOB PAGE HTML:
{job_page_html}

Return ONLY valid JSON with all the extracted information."""

            # Write prompt to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
                tmp_file.write(prompt)
                tmp_path = tmp_file.name

            try:
                print("  🤖 AI analyzing job details and suitability...")
                
                # Run AI extraction with temp file
                result = subprocess.run(
                    f"cat '{tmp_path}' | {self.claude_path}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60  # 60 second timeout
                )
                
                if result.returncode == 0 and result.stdout:
                    try:
                        # Find JSON in response
                        response = result.stdout
                        json_start = response.find('{')
                        json_end = response.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_str = response[json_start:json_end]
                            details = json.loads(json_str)
                            
                            # Print suitability assessment
                            if details.get('is_suitable'):
                                print(f"  ✅ SUITABLE! Score: {details.get('suitability_score', 0)}/100")
                            else:
                                print(f"  ❌ Not suitable. Score: {details.get('suitability_score', 0)}/100")
                            
                            if details.get('suitability_reasons'):
                                print(f"  Reasons: {', '.join(details['suitability_reasons'][:3])}")
                            
                            return details
                        else:
                            print("❌ No JSON found in AI response")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse AI response as JSON: {e}")
                else:
                    print(f"❌ AI analysis failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("❌ AI analysis timed out")
            except Exception as e:
                print(f"❌ AI analysis error: {e}")
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            print(f"❌ Failed to get job details: {e}")
        
        return {}

    async def filter_by_date(self, jobs: list[JobListing], max_days: int = 7) -> list[JobListing]:
        """Filter jobs by posting date."""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=max_days)
        filtered_jobs = []

        for job in jobs:
            if job.posting_date and job.posting_date >= cutoff_date:
                filtered_jobs.append(job)
            elif not job.posting_date:
                # Include if we can't determine date (might be recent)
                filtered_jobs.append(job)

        return filtered_jobs