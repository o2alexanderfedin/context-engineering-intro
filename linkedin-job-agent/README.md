# LinkedIn Job Application Agent

An intelligent, fully automated agent that analyzes resumes, searches LinkedIn for matching positions, and applies to jobs based on configurable criteria.

## Features

- 📄 **Resume Parsing**: Extracts skills and experience from PDF/DOCX files
- 🔍 **Smart Job Search**: AI-powered job matching with Claude
- 🤖 **Browser Automation**: Stealth mode to avoid bot detection
- 📊 **Job Scoring**: Intelligent matching algorithm (>70% relevance)
- 💾 **Application Tracking**: PostgreSQL database for history
- 🚦 **Rate Limiting**: Respects LinkedIn's limits (50 apps/day)
- 🎯 **Location Filtering**: ZIP code radius + high-demand areas
- 📈 **Statistics Dashboard**: Track application metrics

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Chrome/Chromium browser
- Claude CLI (`~/claude-eng`) - optional for AI features

### Installation

1. **Clone the repository**:
```bash
cd linkedin-job-agent
```

2. **Install dependencies with UV**:
```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

3. **Install Playwright browsers**:
```bash
playwright install chromium
```

4. **Start PostgreSQL with Docker**:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

5. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your LinkedIn credentials
```

### Configuration

Edit `.env` file with your settings:

```env
# Required: LinkedIn Credentials
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Job Search Settings
DEFAULT_LOCATION=San Jose, CA
DEFAULT_ZIP_CODE=95128
SEARCH_RADIUS_MILES=50
POSTING_AGE_DAYS=7
MIN_MATCH_SCORE=0.7

# Optional: Claude AI
CLAUDE_ENGINE_PATH=~/claude-eng

# Rate Limiting
DAILY_APPLICATION_LIMIT=50
```

## Usage

### Basic Job Search

Search and apply to jobs based on your resume:

```bash
python -m src.main search --resume path/to/resume.pdf --keywords "Software Engineer" --location "San Francisco, CA"
```

### Command Options

```bash
# Search with specific parameters
python -m src.main search \
  --resume resume.pdf \
  --keywords "Python Developer" \
  --location "Remote" \
  --remote \
  --limit 20 \
  --dry-run  # Preview without applying

# Auto-apply to matched jobs
python -m src.main search \
  --resume resume.pdf \
  --auto-apply \
  --limit 10

# View application statistics
python -m src.main stats

# Initial setup
python -m src.main setup
```

### CLI Options

- `--resume, -r`: Path to resume file (PDF/DOCX) [required]
- `--keywords, -k`: Job search keywords (auto-detected if not provided)
- `--location, -l`: Job location (default from .env)
- `--remote`: Search for remote positions
- `--limit, -n`: Maximum number of jobs to process (default: 10)
- `--dry-run`: Run without actually applying
- `--auto-apply`: Automatically apply to matched jobs
- `--debug`: Enable debug logging

## Project Structure

```
linkedin-job-agent/
├── src/
│   ├── main.py              # CLI interface
│   ├── config.py            # Settings management
│   ├── resume/              # Resume parsing & analysis
│   ├── linkedin/            # Browser automation & scraping
│   ├── matching/            # Job scoring & filtering
│   ├── database/            # PostgreSQL models & repository
│   ├── ai/                  # Claude AI integration
│   └── utils/               # Rate limiting & logging
├── docker/                  # Database setup
├── tests/                   # Test suite
└── logs/                    # Application logs
```

## How It Works

1. **Resume Analysis**: Parses your resume to extract skills, experience, and preferences
2. **AI Enhancement**: Uses Claude to understand context and suggest search terms
3. **Job Search**: Automates LinkedIn search with your criteria
4. **Smart Filtering**: Filters by posting date (≤7 days), location, and work arrangement
5. **Intelligent Matching**: Scores each job based on skill match, title relevance, and location
6. **Application Tracking**: Saves all applications to PostgreSQL for history
7. **Rate Limiting**: Implements human-like delays and daily limits

## Anti-Bot Detection

The agent implements multiple stealth measures:
- Playwright-stealth integration
- Random user agent rotation
- Human-like mouse movements and typing
- Session persistence
- Exponential backoff on rate limits
- Random delays between actions (5-30 seconds)

## Database Schema

Applications are tracked in PostgreSQL:

```sql
CREATE TABLE applications (
    application_id UUID PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE,
    job_title VARCHAR(500),
    company_name VARCHAR(255),
    location VARCHAR(255),
    work_arrangement VARCHAR(50),
    posting_date TIMESTAMP,
    application_date TIMESTAMP,
    status VARCHAR(50),
    match_score NUMERIC(3,2),
    job_url TEXT,
    skills_matched TEXT[]
);
```

## Testing

Run the test suite:

```bash
# All tests
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html

# Specific module
uv run pytest tests/test_resume_parser.py -v
```

## Validation

Run validation checks:

```bash
# Linting
uv run ruff check src/ --fix

# Type checking
uv run mypy src/

# All checks
uv run ruff check src/ && uv run mypy src/ && uv run pytest tests/
```

## Important Notes

### Security
- Never commit `.env` file with credentials
- LinkedIn passwords are never stored in the database
- Use environment variables for all sensitive data
- Consider using a password manager integration

### LinkedIn Terms of Service
- This tool automates browser actions which may violate LinkedIn's ToS
- Use at your own risk and responsibility
- Respect rate limits to avoid account suspension
- Consider LinkedIn's official APIs for production use

### Rate Limiting
- Maximum 50 applications per day (configurable)
- 5-15 second delays between searches
- 10-30 second delays between applications
- Exponential backoff on errors

### Best Practices
- Start with `--dry-run` to preview matches
- Use low limits initially (5-10 jobs)
- Monitor logs for any issues
- Regularly update your resume data
- Review applications in the database

## Troubleshooting

### Common Issues

1. **Login fails**: 
   - Check credentials in `.env`
   - May need manual 2FA completion
   - Try with `HEADLESS_MODE=false` to see browser

2. **No jobs found**:
   - Broaden search keywords
   - Increase location radius
   - Check posting age filter

3. **Rate limiting**:
   - Reduce daily limit
   - Increase delays in config
   - Wait 24 hours to reset

4. **Database connection**:
   - Ensure Docker is running
   - Check PostgreSQL logs
   - Verify connection URL

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Run validation suite
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for educational purposes. Users are responsible for complying with LinkedIn's Terms of Service and applicable laws. The authors are not responsible for any misuse or account suspensions resulting from use of this tool.

## Support

For issues and questions:
- Check logs in `logs/app.log`
- Review the troubleshooting section
- Open an issue on GitHub