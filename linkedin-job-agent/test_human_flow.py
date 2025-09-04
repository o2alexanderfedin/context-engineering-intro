#!/usr/bin/env python3
"""Test the human-like job application flow."""

import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from src.linkedin.human_flow import HumanJobApplicant

async def test_human_flow():
    """Test the human-like application flow."""
    print("Testing Human-Like Job Application Flow")
    print("=" * 50)
    
    # Mock page object
    mock_page = AsyncMock()
    
    # Mock job cards (simulate 3 jobs on the page)
    mock_job1 = MagicMock()
    mock_job2 = MagicMock()
    mock_job3 = MagicMock()
    
    # Setup mock responses
    mock_page.query_selector_all.return_value = [mock_job1, mock_job2, mock_job3]
    mock_page.wait_for_selector = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    
    # Mock job details panel
    mock_detail_panel = AsyncMock()
    mock_detail_panel.inner_html.return_value = """
    <div>
        <h1>Senior Software Engineer</h1>
        <span>Google</span>
        <span>Mountain View, CA</span>
        <p>We are looking for a senior engineer...</p>
    </div>
    """
    mock_page.query_selector.return_value = mock_detail_panel
    
    # Mock AI parser
    mock_ai_parser = Mock()
    mock_ai_parser.match_job.return_value = {
        'match_score': 85,
        'recommendation': 'yes'
    }
    
    # Create applicant
    applicant = HumanJobApplicant(
        page=mock_page,
        resume_text="Alex Fedin - Senior Engineer with 10 years experience",
        ai_parser=mock_ai_parser
    )
    
    # Test the flow (limit to 2 jobs for quick test)
    print("\nStarting application flow...")
    print("-" * 30)
    
    # Mock the click and other async operations
    mock_job1.click = AsyncMock()
    mock_job2.click = AsyncMock()
    mock_job3.click = AsyncMock()
    
    # Override some methods for testing
    async def mock_extract_info(html):
        return {
            'title': 'Senior Software Engineer',
            'company': 'Google',
            'location': 'Mountain View, CA',
            'description': 'Great opportunity'
        }
    
    applicant._extract_job_info_with_ai = mock_extract_info
    
    # Mock apply method to always succeed
    async def mock_apply():
        print("    [TEST] Would apply to job here")
        return True
    
    applicant._apply_to_job = mock_apply
    
    # Mock pagination to return False (no next page)
    async def mock_next_page():
        return False
    
    applicant._go_to_next_page = mock_next_page
    
    # Run the application flow
    result = await applicant.apply_to_jobs(max_jobs=2, min_match_score=0.7)
    
    print(f"\nTest Results:")
    print(f"  Jobs reviewed: {applicant.reviewed_count}")
    print(f"  Applications submitted: {applicant.applied_count}")
    print(f"  Mock job clicks called: {mock_job1.click.called}")
    
    assert applicant.reviewed_count > 0, "Should have reviewed at least one job"
    print("\n✅ Human flow test passed!")

if __name__ == "__main__":
    asyncio.run(test_human_flow())