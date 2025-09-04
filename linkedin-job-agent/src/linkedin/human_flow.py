"""Human-like job application flow for LinkedIn."""

import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import Page
import json
import os
from anthropic import AsyncAnthropic


class HumanJobApplicant:
    """Applies to jobs like a human would - one at a time, reading details first."""
    
    def __init__(self, page: Page, resume_text: str, ai_parser):
        self.page = page
        self.resume_text = resume_text
        self.ai_parser = ai_parser
        self.applied_count = 0
        self.reviewed_count = 0
    
    async def apply_to_jobs(self, max_jobs: int = 50, min_match_score: float = 0.7):
        """Apply to jobs like a human - click, read, decide, apply, repeat."""
        print("\n🧑‍💼 Starting human-like job application process...")
        
        jobs_processed = 0
        page_num = 1
        
        while jobs_processed < max_jobs:
            print(f"\n📄 Page {page_num}")
            
            # Get list of job cards on current page
            job_cards = await self._get_job_cards()
            if not job_cards:
                print("  No jobs found on this page")
                break
            
            print(f"  Found {len(job_cards)} jobs on this page")
            
            # Process each job one by one
            for i, job_card in enumerate(job_cards):
                if jobs_processed >= max_jobs:
                    break
                
                print(f"\n  Job {i+1}/{len(job_cards)}:")
                
                # Click on the job to view details
                job_details = await self._click_and_read_job(job_card)
                if not job_details:
                    print("    ⚠️ Could not read job details")
                    continue
                
                self.reviewed_count += 1
                jobs_processed += 1
                
                # Show what we're looking at
                print(f"    📋 {job_details.get('title', 'Unknown')} at {job_details.get('company', 'Unknown')}")
                print(f"    📍 {job_details.get('location', 'Unknown')}")
                
                # Check if it's Easy Apply
                if not job_details.get('easy_apply', False):
                    print("    ⏭️ Skipping - not Easy Apply")
                    continue
                
                # Ask AI to evaluate the match
                match_score = await self._evaluate_job_match(job_details)
                print(f"    🎯 Match score: {match_score:.0%}")
                
                # Decide whether to apply
                if match_score >= min_match_score:
                    print("    ✅ Good match! Applying...")
                    if await self._apply_to_job():
                        self.applied_count += 1
                        print("    ✓ Application submitted")
                    else:
                        print("    ✗ Could not submit application")
                else:
                    print("    ⏭️ Not a good match, moving on")
                
                # Brief pause between jobs (human-like)
                await self.page.wait_for_timeout(2000)
            
            # Check if we should go to next page
            if jobs_processed < max_jobs:
                if await self._go_to_next_page():
                    page_num += 1
                    await self.page.wait_for_timeout(3000)  # Wait for page load
                else:
                    print("\n📋 No more pages available")
                    break
        
        # Summary
        print(f"\n✅ Job application session complete!")
        print(f"  Jobs reviewed: {self.reviewed_count}")
        print(f"  Applications submitted: {self.applied_count}")
        
        return self.applied_count
    
    async def _get_job_cards(self) -> list:
        """Get all job cards visible on current page."""
        try:
            # Wait for job list to be visible
            jobsList = await self.page.wait_for_selector('.//div[@data-job-id]/ancestor::ul', timeout=5000)
            await self.page.wait_for_selector('div[data-job-id]', timeout=5000)
            
            
            # Get all job cards
            job_cards = await self.page.query_selector_all('div[data-job-id]')
            return job_cards
        except Exception as e:
            print(f"    Error getting job cards: {e}")
            return []
    
    async def _click_and_read_job(self, job_card) -> Optional[Dict[str, Any]]:
        """Click on a job card and extract details from the detail panel."""
        try:
            # Click the job card
            await job_card.click()
            await self.page.wait_for_timeout(3000)  # Wait for details to load
            
            # Extract job details from the detail panel (right side)
            # Try multiple possible selectors for the detail panel
            selectors_to_try = [
                'div.jobs-search__job-details',
                'div.job-details',
                'div.jobs-details',
                'section.jobs-box',
                'div[data-job-details]',
                'main section',  # Generic fallback
            ]
            
            detail_panel = None
            for selector in selectors_to_try:
                try:
                    detail_panel = await self.page.query_selector(selector)
                    if detail_panel:
                        break
                except:
                    continue
            
            if not detail_panel:
                # Try to get any content from the right panel
                detail_panel = await self.page.query_selector('div.scaffold-layout__detail')
                
            if not detail_panel:
                print(f"      Could not find detail panel with any selector")
                return None
            
            # Get the HTML of the detail panel
            detail_html = await detail_panel.inner_html()
            
            # If HTML is too short, it's probably not the right panel
            if len(detail_html) < 100:
                print(f"      Detail panel too short ({len(detail_html)} chars)")
                return None
            
            print(f"      Found detail panel ({len(detail_html)} chars)")
            
            # Use AI to extract structured information
            job_info = await self._extract_job_info_with_ai(detail_html)
            
            if not job_info:
                # Fallback: try to extract basic info manually
                job_info = {
                    'title': 'Unknown Job',
                    'company': 'Unknown Company',
                    'location': 'Unknown',
                    'description': detail_html[:500]
                }
            
            # Check for Easy Apply button
            easy_apply_selectors = [
                'button[aria-label*="Easy Apply"]',
                'button:has-text("Easy Apply")',
                'button.jobs-apply-button',
                'div[class*="easy-apply"]'
            ]
            
            easy_apply = False
            for selector in easy_apply_selectors:
                try:
                    btn = await self.page.query_selector(selector)
                    if btn:
                        easy_apply = True
                        break
                except:
                    pass
            
            job_info['easy_apply'] = easy_apply
            print(f"      Easy Apply: {easy_apply}")
            
            return job_info
            
        except Exception as e:
            print(f"    Error reading job details: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _extract_job_info_with_ai(self, html: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """Use AI to extract job information from HTML with retry logic."""
        # Truncate if too long
        if len(html) > 50000:
            html = html[:50000]
        
        # Initialize Anthropic client if not already done
        if not hasattr(self, '_anthropic_client'):
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                print("      Warning: ANTHROPIC_API_KEY not set, using fallback")
                return {
                    'title': 'Unknown',
                    'company': 'Unknown',
                    'location': 'Unknown',
                    'description': html[:200] if html else 'No description available'
                }
            self._anthropic_client = AsyncAnthropic(api_key=api_key)
        
        for attempt in range(max_retries):
            try:
                prompt = f"""Extract job information from this HTML content.

HTML:
{html}

Look for:
1. Job title (usually in h1 or h2 tags, or elements with title in class/id)
2. Company name (often in a span or div near the title)
3. Location (look for location, workplace-type, or city/state text)
4. Job description (the main body text describing the role)

Return a JSON object with exactly these fields:
{{
  "title": "the job title",
  "company": "the company name",
  "location": "the job location",
  "description": "first 200 characters of job description"
}}

If you cannot find a field, use "Not Found" as the value.
Return ONLY the JSON object, no other text."""

                # Use Claude API
                message = await self._anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                # Extract text content from the response
                response = message.content[0].text if message.content else ""
                print(f"      AI response received ({len(response)} chars)")
                
                # Find JSON in response
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    try:
                        job_info = json.loads(json_str)
                        # Ensure all required fields exist
                        for field in ['title', 'company', 'location', 'description']:
                            if field not in job_info:
                                job_info[field] = 'Not Found'
                        
                        # If we got valid data, return it
                        if job_info.get('title') != 'Unknown' and job_info.get('title') != 'Not Found':
                            print(f"      Successfully extracted: {job_info.get('title')}")
                            return job_info
                            
                    except json.JSONDecodeError as e:
                        print(f"      JSON decode error: {e}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)  # Brief pause before retry
                            continue
                
            except Exception as e:
                print(f"      AI extraction error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
        
        # All retries failed - return fallback
        print(f"      All {max_retries} AI extraction attempts failed, using fallback")
        return {
            'title': 'Unknown',
            'company': 'Unknown',
            'location': 'Unknown',
            'description': html[:200] if html else 'No description available'
        }
    
    async def _evaluate_job_match(self, job_details: Dict[str, Any]) -> float:
        """Use AI to evaluate how well the job matches the resume."""
        try:
            job_text = f"""
Job Title: {job_details.get('title', 'Unknown')}
Company: {job_details.get('company', 'Unknown')}
Location: {job_details.get('location', 'Unknown')}
Description: {job_details.get('description', '')}
Requirements: {job_details.get('requirements', [])}
"""
            
            # Use the AI parser's match_job method
            match_result = await self.ai_parser.match_job(self.resume_text, job_text)
            
            if match_result and isinstance(match_result, dict):
                return match_result.get('match_score', 0) / 100.0
            
            return 0.0
            
        except Exception as e:
            print(f"    Match evaluation error: {e}")
            return 0.0
    
    async def _apply_to_job(self) -> bool:
        """Click Easy Apply and go through the application process."""
        try:
            # Find and click Easy Apply button
            easy_apply_btn = await self.page.query_selector('button[aria-label*="Easy Apply"]')
            if not easy_apply_btn:
                return False
            
            await easy_apply_btn.click()
            await self.page.wait_for_timeout(2000)
            
            # Check if modal opened
            modal = await self.page.query_selector('div[role="dialog"]')
            if not modal:
                return False
            
            # Handle the application flow
            max_steps = 5
            for step in range(max_steps):
                # Check for submit button
                submit_btn = await self.page.query_selector('button[aria-label*="Submit application"]')
                if submit_btn:
                    await submit_btn.click()
                    await self.page.wait_for_timeout(2000)
                    return True
                
                # Check for next button
                next_btn = await self.page.query_selector('button[aria-label*="Continue to next step"]')
                if not next_btn:
                    next_btn = await self.page.query_selector('button:has-text("Next")')
                
                if next_btn:
                    # Check if there are required fields to fill
                    # For now, just click next (in real implementation, would fill fields)
                    await next_btn.click()
                    await self.page.wait_for_timeout(2000)
                else:
                    # Look for review button
                    review_btn = await self.page.query_selector('button[aria-label*="Review your application"]')
                    if review_btn:
                        await review_btn.click()
                        await self.page.wait_for_timeout(2000)
                    else:
                        break
            
            # If we got here without submitting, close the modal
            close_btn = await self.page.query_selector('button[aria-label*="Dismiss"]')
            if close_btn:
                await close_btn.click()
            
            return False
            
        except Exception as e:
            print(f"    Application error: {e}")
            return False
    
    async def _go_to_next_page(self) -> bool:
        """Navigate to the next page of job listings."""
        try:
            # Look for pagination buttons
            next_btn = await self.page.query_selector('button[aria-label="Next"]')
            if not next_btn:
                next_btn = await self.page.query_selector('button[aria-label*="Page 2"]')
            if not next_btn:
                next_btn = await self.page.query_selector('li[class*="selected"] + li button')
            
            if next_btn:
                await next_btn.click()
                await self.page.wait_for_timeout(3000)
                return True
            
            return False
            
        except Exception as e:
            print(f"    Pagination error: {e}")
            return False