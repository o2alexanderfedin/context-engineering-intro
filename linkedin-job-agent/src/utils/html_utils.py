"""HTML to markdown conversion utilities."""

from bs4 import BeautifulSoup
from typing import Optional
import re


def html_to_markdown(html: str, max_length: Optional[int] = None) -> str:
    """
    Convert HTML to simplified markdown format.
    
    Args:
        html: HTML string to convert
        max_length: Maximum length of output markdown (optional)
        
    Returns:
        Markdown formatted string
    """
    if not html:
        return ""
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Process headers
    for i in range(1, 7):
        for header in soup.find_all(f'h{i}'):
            header.string = f"{'#' * i} {header.get_text(strip=True)}\n"
    
    # Process strong/bold
    for strong in soup.find_all(['strong', 'b']):
        text = strong.get_text(strip=True)
        if text:
            strong.string = f"**{text}**"
    
    # Process emphasis/italic
    for em in soup.find_all(['em', 'i']):
        text = em.get_text(strip=True)
        if text:
            em.string = f"*{text}*"
    
    # Process links
    for link in soup.find_all('a'):
        text = link.get_text(strip=True)
        href = link.get('href', '')
        if text and href:
            link.string = f"[{text}]({href})"
    
    # Process lists
    for ul in soup.find_all('ul'):
        for li in ul.find_all('li'):
            text = li.get_text(strip=True)
            if text:
                li.string = f"- {text}\n"
    
    for ol in soup.find_all('ol'):
        for idx, li in enumerate(ol.find_all('li'), 1):
            text = li.get_text(strip=True)
            if text:
                li.string = f"{idx}. {text}\n"
    
    # Process paragraphs
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if text:
            p.string = f"{text}\n\n"
    
    # Process line breaks
    for br in soup.find_all('br'):
        br.replace_with('\n')
    
    # Get text content
    text = soup.get_text()
    
    # Clean up excessive whitespace
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line:
            lines.append(line)
    
    # Join lines with proper spacing
    markdown = '\n'.join(lines)
    
    # Clean up multiple consecutive newlines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
    # Remove leading/trailing whitespace
    markdown = markdown.strip()
    
    # Truncate if max_length specified
    if max_length and len(markdown) > max_length:
        markdown = markdown[:max_length] + "..."
    
    return markdown


def extract_job_sections(html: str) -> dict:
    """
    Extract specific job-related sections from HTML.
    
    Args:
        html: HTML string containing job posting
        
    Returns:
        Dictionary with extracted sections
    """
    soup = BeautifulSoup(html, 'lxml')
    
    sections = {
        'title': '',
        'company': '',
        'location': '',
        'description': '',
        'requirements': '',
        'benefits': ''
    }
    
    # Look for job title - common patterns
    title_selectors = [
        'h1', 'h2',
        '[class*="job-title"]', '[class*="jobTitle"]',
        '[class*="position"]', '[class*="role"]',
        '[data-test*="job-title"]', '[aria-label*="job title"]'
    ]
    
    for selector in title_selectors:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            sections['title'] = element.get_text(strip=True)
            break
    
    # Look for company name
    company_selectors = [
        '[class*="company"]', '[class*="employer"]',
        '[class*="organization"]', '[data-test*="company"]',
        'a[href*="/company/"]'
    ]
    
    for selector in company_selectors:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            sections['company'] = element.get_text(strip=True)
            break
    
    # Look for location
    location_selectors = [
        '[class*="location"]', '[class*="workplace"]',
        '[class*="city"]', '[data-test*="location"]',
        'span[class*="bullet"]:has-text("·")'
    ]
    
    for selector in location_selectors:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            text = element.get_text(strip=True)
            # Filter out non-location text
            if any(keyword in text.lower() for keyword in ['remote', 'hybrid', 'onsite', 'city', 'state']):
                sections['location'] = text
                break
    
    # Look for job description - usually the largest text block
    description_selectors = [
        '[class*="description"]', '[class*="details"]',
        '[class*="job-details"]', '[class*="content"]',
        'article', 'section'
    ]
    
    for selector in description_selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            if len(text) > 100:  # Ensure it's substantial content
                sections['description'] = text[:1000]  # Limit to first 1000 chars
                break
    
    return sections