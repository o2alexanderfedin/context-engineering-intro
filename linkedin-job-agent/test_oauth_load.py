#!/usr/bin/env python3
"""Test OAuth token loading."""

from dotenv import load_dotenv
import os
from src.config import get_settings

# Load .env file
load_dotenv()

# Get settings
settings = get_settings()

print("OAuth token from environment:", "Set" if os.environ.get('CLAUDE_CODE_OAUTH_TOKEN') else "Not set")
print("OAuth token from settings:", "Set" if settings.claude_code_oauth_token else "Not set")
print("Default ZIP code:", settings.default_zip_code)
print("Token starts with:", settings.claude_code_oauth_token[:20] if settings.claude_code_oauth_token else "None")
