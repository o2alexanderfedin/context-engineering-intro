"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.config import Settings
from src.database.models import JobListing, ResumeData


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        linkedin_email="test@example.com",
        linkedin_password="test_pass",
        database_url="postgresql://test:test@localhost/test_db",
        headless_mode=True,
        debug=True,
        dry_run=True,
    )


@pytest.fixture
def sample_resume_data():
    """Create sample resume data."""
    return ResumeData(
        name="John Doe",
        email="john.doe@example.com",
        phone="(555) 123-4567",
        location="San Jose, CA",
        skills=["Python", "JavaScript", "React", "Docker", "AWS"],
        experience=[
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "duration": "2020-2024",
                "description": "Led development of microservices"
            }
        ],
        education=[
            {
                "degree": "BS Computer Science",
                "school": "Stanford University",
                "year": "2020"
            }
        ],
        preferred_roles=["Software Engineer", "Full Stack Developer"]
    )


@pytest.fixture
def sample_job_listing():
    """Create sample job listing."""
    return JobListing(
        job_id="123456",
        job_title="Senior Software Engineer",
        company_name="Example Corp",
        location="San Francisco, CA",
        work_arrangement="hybrid",
        job_url="https://linkedin.com/jobs/view/123456",
        easy_apply=True,
        job_description="Looking for a senior engineer with Python and React experience..."
    )


@pytest.fixture
def mock_browser():
    """Create mock browser."""
    browser = AsyncMock()
    browser.page = AsyncMock()
    browser.initialize = AsyncMock()
    browser.login = AsyncMock(return_value=True)
    browser.search_jobs = AsyncMock()
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_claude_client():
    """Create mock Claude client."""
    client = AsyncMock()
    client.analyze_text = AsyncMock(return_value='{"score": 0.85}')
    client.match_job_to_resume = AsyncMock(return_value=0.85)
    client.analyze_resume = AsyncMock(return_value={
        "skill_level": "senior",
        "top_skills": ["Python", "React"],
        "salary_range": {"min": 120000, "max": 180000}
    })
    return client


@pytest.fixture
def temp_resume_pdf():
    """Create temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        # Write minimal PDF header
        f.write(b"%PDF-1.4\n")
        f.write(b"John Doe\nSoftware Engineer\njohn@example.com\n")
        f.write(b"Python, JavaScript, React\n")
        f.write(b"%%EOF")
        temp_path = f.name

    yield Path(temp_path)

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)
