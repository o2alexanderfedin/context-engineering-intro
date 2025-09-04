## FEATURE:

**LinkedIn Automated Job Application Agent**

An intelligent, fully automated agent that:
1. Analyzes a candidate's resume to extract skills, experience, and preferences
2. Uses browser automation to search LinkedIn for matching job positions
3. Evaluates job postings against criteria (posting date, location, work arrangement)
4. Automatically applies to suitable positions
5. Tracks all applications in a PostgreSQL database
6. Provides detailed reporting and monitoring

## EXAMPLES:

### Resume Analysis Example
```python
# Input: resume.pdf or resume.docx
resume_data = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-0100",
    "location": "San Jose, CA 95128",
    "skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"],
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "Tech Corp",
            "duration": "2020-2024",
            "description": "Led development of microservices architecture..."
        }
    ],
    "education": [
        {
            "degree": "BS Computer Science",
            "school": "Stanford University",
            "year": "2020"
        }
    ],
    "preferred_roles": ["Software Engineer", "Full Stack Developer", "Backend Engineer"]
}
```

### Job Matching Criteria
```python
criteria = {
    "posting_age_days": 7,  # Max 7 days old
    "location": {
        "zip_code": "95128",
        "radius_miles": 50,
        "high_demand_areas": ["San Francisco", "Seattle", "Austin", "New York"]
    },
    "work_arrangements": ["remote", "hybrid", "onsite"],
    "min_match_score": 0.7,  # 70% skills match minimum
    "excluded_companies": [],  # Companies to avoid
    "salary_range": {"min": 100000, "max": None}  # Optional
}
```

### Application Tracking Schema
```sql
-- PostgreSQL schema for tracking applications
CREATE TABLE applications (
    application_id UUID PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE,
    job_title VARCHAR(500),
    company_name VARCHAR(255),
    location VARCHAR(255),
    work_arrangement VARCHAR(50),
    posting_date DATE,
    application_date TIMESTAMP,
    status VARCHAR(50),  -- 'applied', 'saved', 'rejected', 'interview'
    match_score DECIMAL(3,2),
    job_url TEXT,
    job_description TEXT,
    salary_range JSONB,
    skills_matched TEXT[],
    notes TEXT
);
```

## DOCUMENTATION:

### Claude CLI Integration
- **Anthropic Claude CLI Docs**: https://docs.anthropic.com/claude/docs/claude-cli
- **Claude MCP (Model Context Protocol)**: https://modelcontextprotocol.io/
- **Using ~/claude-eng**: Local Claude engine with same syntax as Claude CLI

### Browser Automation
- **Playwright Documentation**: https://playwright.dev/python/
- **Selenium with Chrome**: https://selenium-python.readthedocs.io/
- **Undetected ChromeDriver**: https://github.com/ultrafunkamsterdam/undetected-chromedriver

### LinkedIn Specifics
- **LinkedIn Job Search URL Structure**: Understanding query parameters for job searches
- **LinkedIn Application Forms**: Handling Easy Apply vs external applications
- **Rate Limiting**: LinkedIn's anti-bot measures and how to work within limits
- **Session Management**: Maintaining authenticated sessions

### Resume Parsing
- **PyPDF2/pdfplumber**: For PDF resume extraction
- **python-docx**: For Word document parsing
- **spaCy**: For NLP-based skill extraction
- **Resume Parser Libraries**: pyresparser, resume-parser

### Database & Storage
- **SQLAlchemy with PostgreSQL**: ORM for database operations
- **Docker Postgres Setup**: Container configuration for local database
- **Alembic**: Database migration management

### AI Integration
- **Claude API for Resume Analysis**: Using AI to understand resume context
- **Claude API for Job Matching**: Intelligent matching beyond keyword search
- **Prompt Engineering**: Optimizing prompts for accurate job evaluation

## OTHER CONSIDERATIONS:

### Security & Ethics
- **Never store LinkedIn passwords**: Use secure session management
- **Respect rate limits**: Implement exponential backoff and daily limits
- **User consent**: Ensure user explicitly approves each application
- **Data privacy**: Encrypt sensitive data, use environment variables for credentials
- **Compliance**: Follow LinkedIn's Terms of Service regarding automation

### Technical Architecture
```
linkedin-job-agent/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point with CLI
│   ├── config.py                # Configuration management
│   │
│   ├── resume/
│   │   ├── __init__.py
│   │   ├── parser.py            # Resume parsing logic
│   │   ├── analyzer.py          # AI-powered analysis
│   │   └── tests/
│   │       └── test_parser.py
│   │
│   ├── linkedin/
│   │   ├── __init__.py
│   │   ├── browser.py           # Browser automation
│   │   ├── scraper.py           # Job listing scraper
│   │   ├── applier.py           # Application submission
│   │   └── tests/
│   │       └── test_browser.py
│   │
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── scorer.py            # Job-resume matching
│   │   ├── filters.py           # Criteria filtering
│   │   └── tests/
│   │       └── test_scorer.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── repository.py        # Data access layer
│   │   └── migrations/          # Alembic migrations
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── claude_client.py     # Claude API wrapper
│   │   ├── prompts.py           # Prompt templates
│   │   └── tests/
│   │       └── test_claude.py
│   │
│   └── monitoring/
│       ├── __init__.py
│       ├── logger.py            # Structured logging
│       └── metrics.py           # Application metrics
│
├── docker/
│   ├── docker-compose.yml       # PostgreSQL setup
│   └── init.sql                 # Initial schema
│
├── examples/
│   ├── sample_resume.pdf
│   ├── sample_resume.docx
│   └── config.example.yml
│
├── tests/
│   ├── conftest.py             # Shared fixtures
│   └── integration/            # Integration tests
│
├── .env.example                # Environment variables template
├── pyproject.toml              # UV package management
├── README.md                   # Setup and usage docs
├── CLAUDE.md                   # AI assistant guidelines
├── PLANNING.md                 # Architecture decisions
└── TASK.md                     # Development tasks

```

### Implementation Strategy

1. **Phase 1: Foundation**
   - Set up project structure with UV
   - Configure PostgreSQL with Docker
   - Implement resume parser for PDF/DOCX
   - Create database models and migrations

2. **Phase 2: LinkedIn Integration**
   - Implement secure browser automation
   - Build job search and scraping logic
   - Handle authentication and session management
   - Implement rate limiting and retry logic

3. **Phase 3: Intelligence Layer**
   - Integrate Claude API for resume analysis
   - Build job-resume matching algorithm
   - Implement filtering based on criteria
   - Create scoring and ranking system

4. **Phase 4: Application System**
   - Build Easy Apply automation
   - Handle different application form types
   - Implement application tracking
   - Add safety checks and user confirmation

5. **Phase 5: Polish & Production**
   - Create CLI interface with rich output
   - Add comprehensive logging and monitoring
   - Write integration tests
   - Create deployment documentation

### Key Dependencies
```toml
[project]
dependencies = [
    "playwright>=1.40.0",
    "undetected-chromedriver>=3.5.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.0",
    "alembic>=1.13.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "pypdf2>=3.0.0",
    "pdfplumber>=0.10.0",
    "python-docx>=1.0.0",
    "spacy>=3.7.0",
    "anthropic>=0.18.0",
    "click>=8.1.0",
    "rich>=13.7.0",
    "python-dotenv>=1.0.0",
    "structlog>=24.1.0",
    "httpx>=0.25.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    "schedule>=1.2.0",
    "redis>=5.0.0"  # For caching and rate limiting
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
    "ipdb>=0.13.0"
]
```

### Critical Implementation Notes

1. **Browser Automation Challenges**
   - LinkedIn actively detects and blocks bots
   - Use undetected-chromedriver or Playwright with stealth mode
   - Implement human-like delays and mouse movements
   - Rotate user agents and use residential proxies if needed

2. **Session Management**
   - Store cookies securely for persistent sessions
   - Implement 2FA handling if required
   - Monitor for session expiration and re-authenticate

3. **Rate Limiting Strategy**
   ```python
   # Implement exponential backoff
   class RateLimiter:
       def __init__(self):
           self.daily_limit = 50  # Applications per day
           self.search_delay = (5, 15)  # Random delay between searches
           self.apply_delay = (10, 30)  # Random delay between applications
   ```

4. **Error Recovery**
   - Implement circuit breaker pattern for API calls
   - Save progress frequently to database
   - Allow resuming from last successful point
   - Detailed error logging for debugging

5. **AI Prompt Engineering**
   ```python
   # Example prompt for job matching
   MATCH_PROMPT = """
   Given this resume:
   {resume_text}
   
   And this job description:
   {job_description}
   
   Evaluate the match on:
   1. Required skills alignment (0-10)
   2. Experience level match (0-10)
   3. Industry/domain fit (0-10)
   4. Location compatibility (0-10)
   
   Return a JSON with scores and reasoning.
   """
   ```

6. **Database Optimization**
   - Index frequently queried fields
   - Use connection pooling
   - Implement caching for repeated searches
   - Regular vacuum and analyze for PostgreSQL

7. **Monitoring & Alerting**
   - Track success/failure rates
   - Monitor for LinkedIn UI changes
   - Alert on authentication failures
   - Daily summary reports

8. **Testing Strategy**
   - Mock LinkedIn responses for unit tests
   - Use test accounts for integration tests
   - Implement smoke tests for critical paths
   - Regular regression testing

9. **Deployment Considerations**
   - Use Docker for consistent environment
   - Implement health checks
   - Set up proper logging aggregation
   - Consider using job queue (Celery/RQ) for scalability

10. **Legal & Ethical Guidelines**
    - Include clear disclaimers about automation
    - Respect LinkedIn's robots.txt
    - Don't overwhelm servers
    - Allow users to review before submitting
    - Maintain audit trail of all applications
