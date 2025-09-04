"""
Direct job extraction from LinkedIn HTML.

This module provides a function to extract job listings directly from LinkedIn HTML
as an alternative to AI-powered extraction.
"""

import json
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup


def extract_jobs_from_html(html_content: str) -> List[Dict[str, Any]]:
    """
    Extract job listings from LinkedIn HTML content.
    
    Args:
        html_content: Raw HTML content from LinkedIn jobs page
        
    Returns:
        List of job dictionaries with extracted information
    """
    jobs = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Look for the main job details container
    job_container = soup.find('div', class_='jobs-details__main-content')
    
    if job_container:
        # This appears to be a single job details page
        job_data = _extract_single_job_details(soup)
        if job_data:
            jobs.append(job_data)
    else:
        # Look for multiple job listings
        # Try different selectors for job cards
        job_selectors = [
            '.jobs-semantic-search-job-details-wrapper',
            '.job-card-list__entity',
            '.job-card-container',
            '[data-job-id]'
        ]
        
        for selector in job_selectors:
            job_elements = soup.select(selector)
            for element in job_elements:
                job_data = _extract_job_from_element(element)
                if job_data:
                    jobs.append(job_data)
    
    return jobs


def _extract_single_job_details(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract job details from a single job details page."""
    job_data = {}
    
    try:
        # Extract job ID from URL
        job_id = None
        job_links = soup.find_all('a', href=re.compile(r'/jobs/view/(\d+)'))
        if job_links:
            match = re.search(r'/jobs/view/(\d+)', job_links[0]['href'])
            if match:
                job_id = match.group(1)
        
        # Extract job title
        title_element = soup.find(class_='job-details-jobs-unified-top-card__job-title')
        title = None
        if title_element:
            # Look for h1 within the title element
            h1_element = title_element.find('h1')
            if h1_element:
                link_element = h1_element.find('a')
                title = link_element.get_text(strip=True) if link_element else h1_element.get_text(strip=True)
        
        # Extract company name
        company = None
        company_element = soup.find(class_='job-details-jobs-unified-top-card__company-name')
        if company_element:
            company_link = company_element.find('a')
            company = company_link.get_text(strip=True) if company_link else company_element.get_text(strip=True)
        
        # Extract location and work arrangement
        location = None
        work_arrangement = 'onsite'
        description_container = soup.find(class_='job-details-jobs-unified-top-card__tertiary-description-container')
        if description_container:
            # Location is typically the first span
            spans = description_container.find_all('span', class_='tvm__text')
            for span in spans:
                text = span.get_text(strip=True)
                if any(indicator in text for indicator in ['CA', 'NY', 'Remote', 'United States']):
                    location = text
                    break
        
        # Check for hybrid/remote indicators in preferences
        preferences = soup.find_all(class_='artdeco-button--secondary')
        for pref in preferences:
            pref_text = pref.get_text(strip=True).lower()
            if 'hybrid' in pref_text:
                work_arrangement = 'hybrid'
            elif 'remote' in pref_text:
                work_arrangement = 'remote'
        
        # Extract posted date and applicants
        posted_date = None
        applicants = None
        if description_container:
            text = description_container.get_text()
            # Look for posting date pattern
            posted_match = re.search(r'(Reposted\s+)?(\d+\s+(weeks?|days?|hours?)\s+ago)', text)
            if posted_match:
                posted_date = posted_match.group(2)
            
            # Look for applicants count
            applicant_match = re.search(r'(Over\s+\d+\s+applicants|\d+\s+applicants)', text)
            if applicant_match:
                applicants = applicant_match.group(1)
        
        # Check for Easy Apply button
        easy_apply = bool(soup.find(class_='jobs-apply-button'))
        
        # Construct job URL
        job_url = f"https://linkedin.com/jobs/view/{job_id}" if job_id else None
        
        # Extract salary if available (not present in this example)
        salary = None
        
        job_data = {
            'job_id': job_id,
            'title': title,
            'company': company,
            'location': location,
            'work_arrangement': work_arrangement,
            'salary': salary,
            'posted_date': posted_date,
            'job_url': job_url,
            'easy_apply': easy_apply,
            'applicants': applicants
        }
        
        # Only return if we have essential data
        if job_id and title and company:
            return job_data
            
    except Exception as e:
        print(f"Error extracting job details: {e}")
    
    return None


def _extract_job_from_element(element) -> Dict[str, Any]:
    """Extract job data from a job card element."""
    job_data = {}
    
    try:
        # Extract job ID from data attribute or URL
        job_id = element.get('data-job-id')
        if not job_id:
            job_link = element.find('a', href=re.compile(r'/jobs/view/(\d+)'))
            if job_link:
                match = re.search(r'/jobs/view/(\d+)', job_link['href'])
                if match:
                    job_id = match.group(1)
        
        # Extract other details using similar patterns
        # This would be expanded based on the job card structure
        
        if job_id:
            job_data['job_id'] = job_id
            return job_data
            
    except Exception as e:
        print(f"Error extracting job from element: {e}")
    
    return None


if __name__ == "__main__":
    """Test the extraction with the provided HTML."""
    
    # The HTML content from the user's request
    html_content = '''<div class='extracted-jobs'>
        <div></div>
        
<!---->
    <div class="job-view-layout jobs-details">
      <div>
        <div class="jobs-details__main-content jobs-details__main-content--single-pane full-width
            ">
            

<!---->  
          
          <div>
            
    <div class="t-14" tabindex="-1">
<!---->      <div class="relative
          job-details-jobs-unified-top-card__container--two-pane">
        <div>
          <div class="display-flex align-items-center">
            <div class="display-flex align-items-center flex-1">
                <a class="zbEKRdqtiqGDAWqFuQGprJfrxCENIihQ " aria-label="LinkedIn logo" href="https://www.linkedin.com/company/linkedin/life" data-test-app-aware-link="">
                    
    <div class="ivm-image-view-model   ">
        
    <div class="ivm-view-attr__img-wrapper
        
        ">
<!---->
<!---->          <img width="32" src="https://media.licdn.com/dms/image/v2/C560BAQHaVYd13rRz3A/company-logo_100_100/company-logo_100_100/0/1638831590218/linkedin_logo?e=1759968000&v=beta&t=hDTIv1lTSG7CB32JyBWKFq8Sm6U_5ZC0I-WxFDXleKg" loading="lazy" height="32" alt="LinkedIn logo" id="ember238" class="ivm-view-attr__img--centered EntityPhoto-square-1   evi-image lazy-image ember-view">
    </div>
  
          </div>
  
                </a>

                <div class="job-details-jobs-unified-top-card__company-name" dir="ltr">
                  <a class="zbEKRdqtiqGDAWqFuQGprJfrxCENIihQ " target="_self" tabindex="0" href="https://www.linkedin.com/company/linkedin/life" data-test-app-aware-link=""><!---->LinkedIn<!----></a>
                </div>
            </div>'''
    
    # Extract jobs
    jobs = extract_jobs_from_html(html_content)
    
    print("Extracted jobs:")
    print(json.dumps(jobs, indent=2))