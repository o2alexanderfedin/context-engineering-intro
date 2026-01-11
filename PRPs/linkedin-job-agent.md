name: "LinkedIn Automated Job Application Agent"
description: |

## Purpose
Build a fully automated agent that analyzes resumes, searches LinkedIn for matching positions, and applies to jobs based on configurable criteria. The system integrates with Claude CLI (~/claude-eng), uses PostgreSQL for tracking, and implements robust browser automation with anti-bot measures.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Create a production-ready LinkedIn job application system that:
- Parses resumes (PDF/DOCX) to extract skills and experience
- Uses browser automation to search LinkedIn for jobs
- Filters jobs by posting date (≤7 days), location (95128 zip, 50mi radius), and work arrangement
- Automatically applies to matching positions
- Tracks all applications in PostgreSQL
- Integrates with Claude CLI for AI-powered matching

## Why
- **Business value**: Saves 20+ hours/week of manual job searching and applying
- **Integration**: Leverages Claude AI for intelligent job matching
- **Problems solved**: Automates repetitive job search tasks while maintaining quality

## What
A CLI-based application where users:
1. Provide their resume file path
2. Configure search criteria
3. Run the agent to automatically search and apply
4. Monitor progress via real-time logs
5. Review application history in database

### Success Criteria
- [ ] Resume parser extracts all key information from PDF/DOCX
- [ ] Browser automation bypasses LinkedIn bot detection
- [ ] Job matching achieves >70% relevance score
- [ ] Application submission works for Easy Apply jobs
- [ ] PostgreSQL tracks all applications with full history
- [ ] Claude CLI integration provides intelligent matching
- [ ] Rate limiting prevents account suspension

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://playwright.dev/python/docs/api/class-playwright
  why: Core Playwright API for browser automation
  
- url: https://pypi.org/project/playwright-stealth/
  why: Stealth mode to avoid bot detection (v2.0.0 released June 2025)
  
- url: https://github.com/modelcontextprotocol/python-sdk
  why: MCP SDK for Claude integration - subprocess architecture
  
- url: https://docs.anthropic.com/en/docs/claude-code/mcp
  why: Claude Code MCP integration patterns
  
- url: https://www.sqlalchemy.org/docs/
  why: ORM patterns for PostgreSQL integration
  
- url: https://pdfplumber.readthedocs.io/en/latest/
  why: PDF parsing - most reliable for resumes
  
- url: https://python-docx.readthedocs.io/
  why: DOCX parsing with table support
  
- file: ~/Projects/llm-context-engineering/CLAUDE.md
  why: Project conventions and patterns to follow
  
- file: ~/Projects/llm-context-engineering/INITIAL.md
  why: Feature specification and requirements
```

### Current Codebase tree
```bash
.
├── INITIAL.md              # Feature specification
├── CLAUDE.md              # Coding standards
├── PRPs/                  # Prompt templates
│   └── templates/
│       └── prp_base.md
├── use-cases/             # Example implementations
│   ├── agent-factory-with-subagents/
│   └── pydantic-ai/
└── examples/              # Code examples
```

### Desired Codebase tree with files to be added
```bash
linkedin-job-agent/
├── src/
│   ├── __init__.py                    # Package init
│   ├── main.py                        # CLI entry point
│   ├── config.py                      # Settings management
│   │
│   ├── resume/
│   │   ├── __init__.py
│   │   ├── parser.py                  # PDF/DOCX extraction
│   │   ├── analyzer.py                # Claude AI analysis
│   │   └── tests/
│   │       ├── test_parser.py
│   │       └── test_analyzer.py
│   │
│   ├── linkedin/
│   │   ├── __init__.py
│   │   ├── browser.py                 # Playwright automation
│   │   ├── stealth.py                 # Anti-detection measures
│   │   ├── scraper.py                 # Job listing extraction
│   │   ├── applier.py                 # Application submission
│   │   └── tests/
│   │       ├── test_browser.py
│   │       └── test_scraper.py
│   │
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── scorer.py                  # Job-resume matching
│   │   ├── filters.py                 # Criteria filtering
│   │   └── tests/
│   │       └── test_scorer.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                  # SQLAlchemy models
│   │   ├── repository.py              # Data access layer
│   │   ├── migrations/                # Alembic migrations
│   │   │   └── versions/
│   │   └── tests/
│   │       └── test_repository.py
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── claude_client.py           # Claude CLI wrapper
│   │   ├── prompts.py                 # Prompt templates
│   │   └── tests/
│   │       └── test_claude.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                  # Structured logging
│       ├── rate_limiter.py            # Rate limiting
│       └── tests/
│           └── test_utils.py
│
├── docker/
│   ├── docker-compose.yml             # PostgreSQL setup
│   └── init.sql                       # Initial schema
│
├── tests/
│   ├── conftest.py                    # Shared fixtures
│   └── integration/                   # Integration tests
│       └── test_end_to_end.py
│
├── .env.example                       # Environment template
├── pyproject.toml                     # UV dependencies
├── README.md                          # Setup docs
└── TASK.md                           # Task tracking
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: playwright-stealth v2.0.0 (June 2025) limitations
# - Only bypasses simple bot detection
# - LinkedIn has advanced detection - need multiple strategies
# - Must use with proxies and session management

# CRITICAL: pdfplumber is most reliable for resumes
# - PyPDF2 often fails with complex formatting
# - python-pdfbox works but slower
# - Always handle table extraction separately

# CRITICAL: Claude CLI subprocess pattern
# - Use ~/claude-eng as executable
# - Pass prompts via stdin, not arguments
# - Parse JSON responses from stdout

# CRITICAL: PostgreSQL with Docker
# - Use connection pooling (max 20 connections)
# - UUID primary keys for all tables
# - JSONB for flexible skill/criteria storage

# CRITICAL: LinkedIn rate limits
# - Max 50 applications/day
# - 5-15 second delays between searches
# - 10-30 second delays between applications
# - Exponential backoff on 429 errors
```

## Implementation Blueprint

### Data models and structure

```python
# SQLAlchemy models with proper naming conventions
from sqlalchemy import Column, String, UUID, DateTime, JSONB, Numeric, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Application(Base):
    __tablename__ = 'applications'
    
    application_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    job_id = Column(String(255), unique=True, nullable=False)
    job_title = Column(String(500), nullable=False)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255))
    work_arrangement = Column(String(50))  # remote/hybrid/onsite
    posting_date = Column(DateTime)
    application_date = Column(DateTime)
    status = Column(String(50))  # applied/saved/rejected/interview
    match_score = Column(Numeric(3, 2))
    job_url = Column(Text)
    job_description = Column(Text)
    salary_range = Column(JSONB)
    skills_matched = Column(ARRAY(Text))
    notes = Column(Text)

# Pydantic models for validation
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime

class ResumeData(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: str
    skills: List[str]
    experience: List[Dict[str, str]]
    education: List[Dict[str, str]]
    preferred_roles: List[str] = []

class JobCriteria(BaseModel):
    posting_age_days: int = Field(default=7, le=30)
    location: Dict[str, Any] = Field(default_factory=lambda: {
        "zip_code": "95128",
        "radius_miles": 50,
        "high_demand_areas": ["San Francisco", "Seattle", "Austin", "New York"]
    })
    work_arrangements: List[str] = ["remote", "hybrid", "onsite"]
    min_match_score: float = Field(default=0.7, ge=0.0, le=1.0)
    excluded_companies: List[str] = []
    salary_range: Optional[Dict[str, Optional[int]]] = None
```

### List of tasks to be completed in order

```yaml
Task 1: Project Setup and Dependencies
CREATE pyproject.toml:
  - Add all dependencies from INITIAL.md
  - Configure UV for Python 3.11+
  - Set up ruff and mypy configurations

CREATE src/__init__.py and package structure:
  - Initialize all module directories
  - Add __init__.py files
  - Set up logging configuration

Task 2: Database Setup
CREATE docker/docker-compose.yml:
  - PostgreSQL 15+ container
  - Port 5432 exposed
  - Volume for persistence

CREATE docker/init.sql:
  - Applications table schema
  - Indexes on job_id, application_date
  - UUID extension

CREATE src/database/models.py:
  - SQLAlchemy Base and models
  - Follow CLAUDE.md naming conventions

CREATE src/database/repository.py:
  - CRUD operations for applications
  - Connection pooling setup
  - Error handling

Task 3: Resume Parser Module
CREATE src/resume/parser.py:
  - PDF extraction with pdfplumber
  - DOCX extraction with python-docx
  - Text cleaning and normalization
  - Skill extraction with regex/NLP

CREATE src/resume/analyzer.py:
  - Claude CLI integration
  - Prompt for resume analysis
  - JSON response parsing
  - Error handling

Task 4: LinkedIn Browser Automation
CREATE src/linkedin/browser.py:
  - Playwright setup with stealth
  - Login session management
  - Cookie persistence
  - Error recovery

CREATE src/linkedin/stealth.py:
  - playwright-stealth integration
  - User agent rotation
  - Mouse movement simulation
  - Viewport randomization

CREATE src/linkedin/scraper.py:
  - Job search URL construction
  - Listing extraction
  - Pagination handling
  - Data validation

Task 5: Job Matching Engine
CREATE src/matching/scorer.py:
  - Skill matching algorithm
  - Experience level scoring
  - Location compatibility
  - Weighted scoring

CREATE src/matching/filters.py:
  - Date filtering (≤7 days)
  - Location filtering (radius)
  - Work arrangement filtering
  - Company exclusion

Task 6: Application Submission
CREATE src/linkedin/applier.py:
  - Easy Apply detection
  - Form field mapping
  - Application submission
  - Confirmation validation

Task 7: AI Integration
CREATE src/ai/claude_client.py:
  - Subprocess management for ~/claude-eng
  - Prompt construction
  - Response parsing
  - Error handling

CREATE src/ai/prompts.py:
  - Resume analysis prompt
  - Job matching prompt
  - Cover letter prompt (optional)

Task 8: CLI Interface
CREATE src/main.py:
  - Click CLI setup
  - Command structure
  - Configuration loading
  - Progress display

CREATE src/config.py:
  - Pydantic settings
  - Environment variables
  - Default values
  - Validation

Task 9: Rate Limiting and Utils
CREATE src/utils/rate_limiter.py:
  - Token bucket implementation
  - Daily limits (50 apps/day)
  - Exponential backoff
  - Circuit breaker

CREATE src/utils/logger.py:
  - Structured logging setup
  - Log levels configuration
  - File and console outputs
  - Request/response logging

Task 10: Testing Suite
CREATE tests/conftest.py:
  - Pytest fixtures
  - Mock browser setup
  - Test database
  - Sample data

CREATE all test files:
  - Unit tests for each module
  - Integration tests
  - Mock LinkedIn responses
  - Error case coverage
```

### Per task pseudocode

```python
# Task 3: Resume Parser Implementation
# src/resume/parser.py
import pdfplumber
from docx import Document
from typing import Dict, List, Optional
import re

class ResumeParser:
    def parse(self, file_path: str) -> ResumeData:
        # PATTERN: File extension detection
        if file_path.endswith('.pdf'):
            text = self._extract_pdf(file_path)
        elif file_path.endswith('.docx'):
            text = self._extract_docx(file_path)
        else:
            raise ValueError("Unsupported file format")
        
        # GOTCHA: Clean text before parsing
        text = self._clean_text(text)
        
        # Extract components
        return ResumeData(
            name=self._extract_name(text),
            email=self._extract_email(text),
            phone=self._extract_phone(text),
            location=self._extract_location(text),
            skills=self._extract_skills(text),
            experience=self._extract_experience(text),
            education=self._extract_education(text)
        )
    
    def _extract_pdf(self, path: str) -> str:
        # CRITICAL: pdfplumber handles tables better
        with pdfplumber.open(path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
                # Handle tables separately
                tables = page.extract_tables()
                for table in tables:
                    text += self._table_to_text(table)
        return text

# Task 4: LinkedIn Browser with Stealth
# src/linkedin/browser.py
import asyncio
from playwright.async_api import async_playwright, Browser, Page
from playwright_stealth import stealth_async
import json

class LinkedInBrowser:
    def __init__(self, config: Config):
        self.config = config
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
    
    async def initialize(self):
        # PATTERN: Headful mode for development, headless for production
        playwright = await async_playwright().start()
        
        # CRITICAL: Launch args for stealth
        self.browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # Create context with saved cookies if available
        if self._has_saved_session():
            cookies = self._load_cookies()
            self.context = await self.browser.new_context(
                storage_state=cookies,
                viewport={'width': 1920, 'height': 1080},
                user_agent=self._get_random_user_agent()
            )
        else:
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self._get_random_user_agent()
            )
        
        self.page = await self.context.new_page()
        
        # CRITICAL: Apply stealth to avoid detection
        await stealth_async(self.page)
        
        # Add human-like behavior
        await self._add_human_behavior()
    
    async def _add_human_behavior(self):
        # Random mouse movements
        await self.page.evaluate('''
            () => {
                let mouseX = 0, mouseY = 0;
                document.onmousemove = (e) => {
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                };
                
                setInterval(() => {
                    const event = new MouseEvent('mousemove', {
                        clientX: mouseX + Math.random() * 10 - 5,
                        clientY: mouseY + Math.random() * 10 - 5
                    });
                    document.dispatchEvent(event);
                }, Math.random() * 3000 + 2000);
            }
        ''')

# Task 5: Job Matching with Claude
# src/ai/claude_client.py
import subprocess
import json
from typing import Dict, Any

class ClaudeClient:
    def __init__(self, engine_path: str = "~/claude-eng"):
        self.engine_path = os.path.expanduser(engine_path)
    
    def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        # PATTERN: Subprocess communication with Claude
        prompt = self._build_resume_prompt(resume_text)
        
        # CRITICAL: Use subprocess with proper encoding
        process = subprocess.Popen(
            [self.engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=prompt)
        
        if process.returncode != 0:
            raise RuntimeError(f"Claude engine error: {stderr}")
        
        # Parse JSON response
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            # Fallback to text parsing
            return self._parse_text_response(stdout)
    
    def match_job(self, resume: ResumeData, job_desc: str) -> float:
        prompt = f"""
        Analyze this job match:
        
        Resume Skills: {', '.join(resume.skills)}
        Resume Experience: {len(resume.experience)} positions
        
        Job Description: {job_desc[:1000]}
        
        Return a match score (0-1) as JSON: {{"score": 0.85, "reason": "..."}}
        """
        
        response = self._call_claude(prompt)
        return response.get('score', 0.0)

# Task 9: Rate Limiter
# src/utils/rate_limiter.py
import time
from typing import Optional
import asyncio

class RateLimiter:
    def __init__(self, daily_limit: int = 50):
        self.daily_limit = daily_limit
        self.applications_today = 0
        self.last_reset = time.time()
        self.search_delay = (5, 15)  # seconds
        self.apply_delay = (10, 30)  # seconds
    
    async def acquire_search(self):
        # PATTERN: Random delay for human-like behavior
        delay = random.uniform(*self.search_delay)
        await asyncio.sleep(delay)
    
    async def acquire_apply(self):
        # Check daily limit
        self._check_reset()
        if self.applications_today >= self.daily_limit:
            raise RateLimitExceeded("Daily application limit reached")
        
        delay = random.uniform(*self.apply_delay)
        await asyncio.sleep(delay)
        self.applications_today += 1
    
    def _check_reset(self):
        # Reset counter daily
        if time.time() - self.last_reset > 86400:  # 24 hours
            self.applications_today = 0
            self.last_reset = time.time()
```

### Integration Points
```yaml
DATABASE:
  - migration: "alembic init alembic"
  - command: "alembic revision --autogenerate -m 'Initial schema'"
  - apply: "alembic upgrade head"
  
CONFIG:
  - add to: .env
  - pattern: |
      DATABASE_URL=postgresql://user:pass@localhost/linkedin_jobs
      LINKEDIN_EMAIL=your_email@example.com
      LINKEDIN_PASSWORD=your_password
      CLAUDE_ENGINE_PATH=~/claude-eng
      HEADLESS_MODE=false
      DAILY_APPLICATION_LIMIT=50
  
CLI:
  - command: "python -m src.main --resume path/to/resume.pdf"
  - options: "--dry-run, --verbose, --limit N"
  
DOCKER:
  - start: "docker-compose up -d"
  - logs: "docker-compose logs -f postgres"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd linkedin-job-agent
uv sync  # Install dependencies

ruff check src/ --fix    # Auto-fix style issues
mypy src/                # Type checking

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```python
# Test resume parser
def test_parse_pdf_resume():
    """Test PDF resume extraction"""
    parser = ResumeParser()
    result = parser.parse("tests/fixtures/sample_resume.pdf")
    assert result.name == "John Doe"
    assert "Python" in result.skills
    assert len(result.experience) > 0

# Test rate limiter
def test_rate_limiter_daily_limit():
    """Test daily application limit"""
    limiter = RateLimiter(daily_limit=5)
    for i in range(5):
        limiter.applications_today = i
        limiter.acquire_apply()  # Should pass
    
    with pytest.raises(RateLimitExceeded):
        limiter.acquire_apply()  # Should fail on 6th

# Test Claude integration
@mock.patch('subprocess.Popen')
def test_claude_analyze_resume(mock_popen):
    """Test Claude resume analysis"""
    mock_popen.return_value.communicate.return_value = (
        '{"skills": ["Python", "Docker"], "score": 0.85}',
        ''
    )
    mock_popen.return_value.returncode = 0
    
    client = ClaudeClient()
    result = client.analyze_resume("Resume text...")
    assert result['score'] == 0.85
```

```bash
# Run unit tests
uv run pytest tests/ -v --cov=src --cov-report=html

# If failing: Read errors, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start services
docker-compose up -d
uv run alembic upgrade head

# Test database connection
uv run python -c "from src.database import test_connection; test_connection()"

# Test browser automation (dry run)
uv run python -m src.main --resume tests/fixtures/sample_resume.pdf --dry-run

# Expected: System initializes, parses resume, shows dry run output
# If error: Check logs at logs/app.log
```

### Level 4: End-to-End Test
```bash
# Full system test with mock LinkedIn
uv run python tests/integration/test_end_to_end.py

# Manual browser test
uv run python -m src.main \
  --resume ~/Documents/my_resume.pdf \
  --limit 1 \
  --verbose

# Monitor logs
tail -f logs/app.log
```

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check src/`
- [ ] No type errors: `uv run mypy src/`
- [ ] Database migrations applied: `uv run alembic upgrade head`
- [ ] Docker services running: `docker-compose ps`
- [ ] Resume parser works for PDF and DOCX
- [ ] Browser automation launches without detection
- [ ] Rate limiting prevents excessive requests
- [ ] Claude integration returns valid scores
- [ ] Applications saved to database
- [ ] CLI provides clear feedback

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode LinkedIn credentials - use environment variables
- ❌ Don't skip stealth measures - LinkedIn will block you
- ❌ Don't ignore rate limits - account will be suspended
- ❌ Don't parse resumes with PyPDF2 - use pdfplumber
- ❌ Don't use synchronous browser automation - use async
- ❌ Don't catch all exceptions - be specific
- ❌ Don't apply without user confirmation in production
- ❌ Don't store passwords in plain text
- ❌ Don't use datacenter proxies - use residential
- ❌ Don't make requests without delays

## Critical Production Notes

### Security
```python
# NEVER store LinkedIn password in code or database
# Use secure credential management
from cryptography.fernet import Fernet

class SecureConfig:
    def __init__(self):
        self.cipher = Fernet(self._get_or_create_key())
    
    def encrypt_password(self, password: str) -> bytes:
        return self.cipher.encrypt(password.encode())
    
    def decrypt_password(self, encrypted: bytes) -> str:
        return self.cipher.decrypt(encrypted).decode()
```

### Session Management
```python
# Save and restore browser sessions
async def save_session(page: Page):
    storage = await page.context.storage_state()
    with open('.session.json', 'w') as f:
        json.dump(storage, f)

async def restore_session(browser: Browser):
    if os.path.exists('.session.json'):
        with open('.session.json', 'r') as f:
            storage = json.load(f)
        return await browser.new_context(storage_state=storage)
```

### Error Recovery
```python
# Implement circuit breaker for resilience
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpen()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

## Confidence Score: 8/10

### Scoring Rationale:
- ✅ Comprehensive context with all necessary documentation links
- ✅ Detailed implementation blueprint with pseudocode
- ✅ Clear validation gates and testing strategy
- ✅ Production-ready security and error handling patterns
- ✅ Complete file structure and task breakdown
- ✅ Known gotchas and library quirks documented
- ⚠️ -1: LinkedIn's anti-bot measures are constantly evolving
- ⚠️ -1: Claude CLI integration may need adjustment based on actual ~/claude-eng behavior

The PRP provides sufficient context for one-pass implementation with iterative refinement through the validation loops. The main challenges will be LinkedIn's bot detection and the Claude CLI integration, but the PRP includes fallback strategies and error handling for these scenarios.