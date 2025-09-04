#!/bin/bash

# LinkedIn Job Agent - Run Script
# Automated job search with Alexander Fedin's resume

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Resume path
RESUME="/Users/alexanderfedin/Library/CloudStorage/OneDrive-Personal/Resumes/AlexanderFedin-AI_2025-01-21.pdf"

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    LinkedIn Job Agent - Automated Job Application${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo

# Check if resume exists
if [ ! -f "$RESUME" ]; then
    echo -e "${YELLOW}⚠️  Resume not found: $RESUME${NC}"
    exit 1
fi

# Check if Chrome is running with debugging port
if ! lsof -ti:9222 > /dev/null 2>&1; then
    echo -e "${YELLOW}Chrome is not running with debugging port. Launching visible Chrome...${NC}"
    ./launch_visible_browser.sh > /dev/null 2>&1 &
    sleep 5  # Wait for Chrome to start
    echo -e "${GREEN}✓ Chrome launched and visible${NC}"
else
    echo -e "${GREEN}✓ Chrome is already running on port 9222${NC}"
    # Bring Chrome to foreground
    osascript -e 'tell application "Google Chrome" to activate' 2>/dev/null || true
fi

# Check if PostgreSQL is running
if ! docker compose -f docker/docker-compose.yml ps | grep -q "linkedin_jobs_db.*healthy"; then
    echo -e "${YELLOW}Starting PostgreSQL database...${NC}"
    cd docker && docker compose up -d && cd ..
    sleep 3
fi

echo -e "${GREEN}✓ Resume found: $(basename "$RESUME")${NC}"
echo -e "${GREEN}✓ Database is running${NC}"
echo -e "${GREEN}✓ Browser is visible and ready${NC}"
echo

# Parse arguments
COMMAND=${1:-search}
shift || true

case "$COMMAND" in
    search)
        echo -e "${BLUE}Starting job search and application...${NC}"
        echo -e "${YELLOW}Search criteria:${NC}"
        echo "  • Location: San Jose, CA"
        echo "  • Posted: Last 7 days"
        echo "  • Match score: ≥ 0.7"
        echo "  • Daily limit: 50 applications"
        echo
        
        # Run search with additional parameters
        uv run python -m src.main search \
            --resume "$RESUME" \
            --keywords "${1:-Software Engineer AI ML}" \
            --location "San Jose, CA" \
            --auto-apply \
            "$@"
        ;;
        
    recommended)
        echo -e "${BLUE}Getting recommended jobs (no keyword search)...${NC}"
        # Use empty keywords to trigger recommended jobs URL
        uv run python -m src.main search \
            --resume "$RESUME" \
            --keywords "" \
            --auto-apply \
            "$@"
        ;;
        
    search-only)
        echo -e "${BLUE}Searching jobs (no auto-apply)...${NC}"
        uv run python -m src.main search \
            --resume "$RESUME" \
            --keywords "${1:-Software Engineer AI ML}" \
            --location "San Jose, CA" \
            "$@"
        ;;
        
    stats)
        echo -e "${BLUE}Application Statistics:${NC}"
        uv run python -m src.main stats
        ;;
        
    setup)
        echo -e "${BLUE}Running setup...${NC}"
        uv run python -m src.main setup
        ;;
        
    test)
        echo -e "${BLUE}Testing with dry run (no actual applications)...${NC}"
        echo -e "${YELLOW}NOTE: Browser will open in visible mode for testing${NC}"
        HEADLESS_MODE=false uv run python -m src.main search \
            --resume "$RESUME" \
            --keywords "Software Engineer" \
            --dry-run \
            --limit 50
        ;;
        
    *)
        echo -e "${YELLOW}Usage: $0 [command] [options]${NC}"
        echo
        echo "Commands:"
        echo "  search       - Search and auto-apply to matching jobs (default)"
        echo "  recommended  - Get LinkedIn's recommended jobs (no keyword search)"
        echo "  search-only  - Search without auto-applying"
        echo "  stats        - Show application statistics"
        echo "  setup        - Run initial setup"
        echo "  test         - Test with dry run (no applications)"
        echo
        echo "Examples:"
        echo "  $0                              # Run default search"
        echo "  $0 search \"Senior Engineer\"     # Search with custom keywords"
        echo "  $0 search-only                  # Just search, don't apply"
        echo "  $0 test                         # Test run without applying"
        ;;
esac

echo
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"