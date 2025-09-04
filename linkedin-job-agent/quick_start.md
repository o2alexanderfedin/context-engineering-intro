# Quick Start Guide

## Run Job Search

Your resume is configured: `AlexanderFedin-AI_2025-01-21.pdf`

### Basic Commands:

```bash
# Full automated search and apply
./run_job_search.sh

# Search with custom keywords
./run_job_search.sh search "Machine Learning Engineer"

# Search only (no auto-apply)
./run_job_search.sh search-only

# Test run (dry run, no actual applications)
./run_job_search.sh test

# View statistics
./run_job_search.sh stats
```

### What it does:
1. ✅ Uses your resume from OneDrive
2. ✅ Logs into LinkedIn with configured credentials
3. ✅ Searches for jobs in 95128 area (50 mile radius)
4. ✅ Filters jobs posted in last 7 days
5. ✅ Applies to jobs with ≥0.7 match score
6. ✅ Respects 50 applications/day limit
7. ✅ Uses human-like delays to avoid detection

### Safety Features:
- Rate limiting prevents too many applications
- Random delays between actions
- Circuit breaker stops on repeated failures
- Dry run mode for testing

### Monitor Progress:
The script will show:
- Jobs found
- Match scores
- Application status
- Any errors encountered

### Stop Anytime:
Press `Ctrl+C` to stop the script safely.