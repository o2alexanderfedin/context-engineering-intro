"""SQLAlchemy database models for LinkedIn Job Agent."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import text

Base = declarative_base()


class Application(Base):
    """Database model for job applications."""

    __tablename__ = "applications"

    application_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(String(255), unique=True, nullable=False)
    job_title = Column(String(500), nullable=False)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255))
    work_arrangement = Column(String(50))  # remote/hybrid/onsite
    posting_date = Column(DateTime)
    application_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")  # applied/saved/rejected/interview
    match_score = Column(Numeric(3, 2))
    job_url = Column(Text)
    job_description = Column(Text)
    salary_range = Column(JSONB)
    skills_matched = Column(ARRAY(Text))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic models for validation
class ResumeData(BaseModel):
    """Parsed resume data model."""

    name: str
    email: str
    phone: str | None = None
    location: str
    skills: list[str]
    experience: list[dict[str, str]]
    education: list[dict[str, str]]
    preferred_roles: list[str] = Field(default_factory=list)


class JobCriteria(BaseModel):
    """Job search criteria model."""

    posting_age_days: int = Field(default=7, le=30)
    location: dict[str, Any] = Field(
        default_factory=lambda: {
            "zip_code": "95128",
            "radius_miles": 50,
            "high_demand_areas": ["San Francisco", "Seattle", "Austin", "New York"],
        }
    )
    work_arrangements: list[str] = Field(
        default_factory=lambda: ["remote", "hybrid", "onsite"]
    )
    min_match_score: float = Field(default=0.7, ge=0.0, le=1.0)
    excluded_companies: list[str] = Field(default_factory=list)
    salary_range: dict[str, int | None] | None = None

    @field_validator("work_arrangements")
    @classmethod
    def validate_work_arrangements(cls, v: list[str]) -> list[str]:
        """Validate work arrangement values."""
        valid_arrangements = {"remote", "hybrid", "onsite"}
        for arrangement in v:
            if arrangement.lower() not in valid_arrangements:
                raise ValueError(f"Invalid work arrangement: {arrangement}")
        return [a.lower() for a in v]


class JobListing(BaseModel):
    """Job listing data model."""

    job_id: str
    job_title: str
    company_name: str
    location: str | None = None
    work_arrangement: str | None = None
    posting_date: datetime | None = None
    job_url: str
    job_description: str | None = None
    salary_range: dict[str, Any] | None = None
    easy_apply: bool = False


class ApplicationCreate(BaseModel):
    """Model for creating new application records."""

    job_id: str
    job_title: str
    company_name: str
    location: str | None = None
    work_arrangement: str | None = None
    posting_date: datetime | None = None
    job_url: str
    job_description: str | None = None
    match_score: float | None = None
    salary_range: dict[str, Any] | None = None
    skills_matched: list[str] | None = None
    notes: str | None = None
    status: str = "pending"


class ApplicationUpdate(BaseModel):
    """Model for updating application records."""

    status: str | None = None
    notes: str | None = None
    match_score: float | None = None
    skills_matched: list[str] | None = None


def get_database_url(
    user: str = "linkedin_user",
    password: str = "linkedin_pass",
    host: str = "localhost",
    port: int = 5432,
    database: str = "linkedin_jobs",
) -> str:
    """Construct database URL from components."""
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def create_session(database_url: str) -> Session:
    """Create a database session."""
    engine = create_engine(database_url, pool_size=20, max_overflow=0)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_connection(database_url: str | None = None) -> bool:
    """Test database connection."""
    if not database_url:
        database_url = get_database_url()

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
