"""Basic tests for LinkedIn Job Agent."""


from src.config import Settings
from src.database.models import JobCriteria, ResumeData


def test_settings_creation():
    """Test that settings can be created."""
    settings = Settings()
    assert settings.app_name == "LinkedIn Job Agent"
    assert settings.daily_application_limit == 50


def test_resume_data_model():
    """Test ResumeData model creation."""
    resume = ResumeData(
        name="John Doe",
        email="john@example.com",
        location="San Jose, CA",
        skills=["Python", "JavaScript"],
        experience=[],
        education=[]
    )
    assert resume.name == "John Doe"
    assert len(resume.skills) == 2


def test_job_criteria_validation():
    """Test JobCriteria model validation."""
    criteria = JobCriteria()
    assert criteria.posting_age_days == 7
    assert criteria.min_match_score == 0.7
    assert "remote" in criteria.work_arrangements
