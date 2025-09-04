"""Configuration management for LinkedIn Job Agent."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application settings
    app_name: str = "LinkedIn Job Agent"
    debug: bool = False

    # Database settings
    database_url: str = Field(
        default="postgresql://linkedin_user:linkedin_pass@localhost:5432/linkedin_jobs",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = Field(default=20, ge=1, le=100)

    # LinkedIn settings
    linkedin_email: str = Field(default="", description="LinkedIn email address")
    linkedin_password: str = Field(default="", description="LinkedIn password")
    headless_mode: bool = Field(default=False, description="Run browser in headless mode")

    # Claude AI settings
    claude_engine_path: str = Field(
        default="~/claude-eng",
        description="Path to Claude engine executable",
    )
    claude_api_key: str | None = Field(default=None, description="Claude API key if needed")
    claude_code_oauth_token: str | None = Field(default=None, description="Claude Code OAuth token for long-lived authentication")

    # Job search settings
    default_location: str = Field(default="San Jose, CA", description="Default search location")
    default_zip_code: str = Field(default="95128", description="Default ZIP code")
    search_radius_miles: int = Field(default=50, ge=0, le=200)
    posting_age_days: int = Field(default=7, ge=1, le=30)
    min_match_score: float = Field(default=0.7, ge=0.0, le=1.0)

    # Rate limiting settings
    daily_application_limit: int = Field(default=50, ge=1, le=100)
    search_delay_min: float = Field(default=5.0, ge=1.0)
    search_delay_max: float = Field(default=15.0, ge=2.0)
    apply_delay_min: float = Field(default=10.0, ge=5.0)
    apply_delay_max: float = Field(default=30.0, ge=10.0)

    # Proxy settings (optional)
    proxy_url: str | None = Field(default=None, description="Proxy server URL")
    proxy_username: str | None = Field(default=None, description="Proxy username")
    proxy_password: str | None = Field(default=None, description="Proxy password")

    # File paths
    session_file: Path = Field(default=Path(".linkedin_session.json"))
    log_file: Path = Field(default=Path("logs/app.log"))

    # Feature flags
    dry_run: bool = Field(default=False, description="Run without actually applying")
    auto_apply: bool = Field(default=False, description="Automatically apply to matched jobs")
    save_only: bool = Field(default=False, description="Only save jobs, don't apply")

    @property
    def database_url_masked(self) -> str:
        """Return database URL with masked password."""
        if "@" in self.database_url:
            parts = self.database_url.split("@")
            creds = parts[0].split("://")[1]
            user = creds.split(":")[0]
            return f"postgresql://{user}:****@{parts[1]}"
        return self.database_url

    def validate_credentials(self) -> bool:
        """Validate that required credentials are set."""
        if not self.linkedin_email or not self.linkedin_password:
            return False
        return True

    def get_search_delays(self) -> tuple[float, float]:
        """Get search delay range."""
        return (self.search_delay_min, self.search_delay_max)

    def get_apply_delays(self) -> tuple[float, float]:
        """Get apply delay range."""
        return (self.apply_delay_min, self.apply_delay_max)


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def create_env_example() -> None:
    """Create example .env file."""
    env_example = """# LinkedIn Job Agent Configuration

# Database
DATABASE_URL=postgresql://linkedin_user:linkedin_pass@localhost:5432/linkedin_jobs
DATABASE_POOL_SIZE=20

# LinkedIn Credentials (Required)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Browser Settings
HEADLESS_MODE=false

# Claude AI
CLAUDE_ENGINE_PATH=~/claude-eng
# CLAUDE_API_KEY=your_api_key_if_needed

# Job Search Defaults
DEFAULT_LOCATION=San Jose, CA
DEFAULT_ZIP_CODE=95128
SEARCH_RADIUS_MILES=50
POSTING_AGE_DAYS=7
MIN_MATCH_SCORE=0.7

# Rate Limiting
DAILY_APPLICATION_LIMIT=50
SEARCH_DELAY_MIN=5.0
SEARCH_DELAY_MAX=15.0
APPLY_DELAY_MIN=10.0
APPLY_DELAY_MAX=30.0

# Proxy Settings (Optional)
# PROXY_URL=http://proxy.example.com:8080
# PROXY_USERNAME=proxy_user
# PROXY_PASSWORD=proxy_pass

# Feature Flags
DRY_RUN=false
AUTO_APPLY=false
SAVE_ONLY=false

# Debug Mode
DEBUG=false
"""

    with open(".env.example", "w") as f:
        f.write(env_example)


if __name__ == "__main__":
    # Create example env file if running directly
    create_env_example()
    print("Created .env.example file")
