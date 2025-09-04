#!/usr/bin/env python3
"""Test connecting to existing browser session."""

import asyncio
from src.linkedin.browser import LinkedInBrowser
from src.config import Settings

async def test_connection():
    """Test browser connection."""
    print("Testing browser connection...")
    print("-" * 50)
    
    settings = Settings()
    browser = LinkedInBrowser(settings)
    
    try:
        # Initialize - will try to connect to existing browser first
        await browser.initialize()
        
        # Check if logged in
        logged_in = await browser.check_logged_in()
        
        if logged_in:
            print("✅ Successfully connected and logged in to LinkedIn!")
            print(f"Current URL: {browser.page.url}")
            
            # Get profile name
            try:
                profile_element = await browser.page.query_selector(".global-nav__me-photo")
                if profile_element:
                    print("✅ Profile detected - ready to search for jobs")
            except:
                pass
        else:
            print("❌ Not logged in to LinkedIn")
            print("Please log in manually in your browser")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Don't close the browser if it's an existing session
        if browser.browser:
            try:
                # Check if it's connected via CDP
                contexts = browser.browser.contexts
                if contexts and len(contexts) > 0:
                    print("\n✅ Keeping existing browser session open")
                else:
                    await browser.close()
            except:
                await browser.close()

if __name__ == "__main__":
    print("""
═══════════════════════════════════════════════════════════
    LinkedIn Browser Connection Test
═══════════════════════════════════════════════════════════

INSTRUCTIONS:
1. First, start Chrome with debugging enabled:
   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222

2. Log into LinkedIn in that Chrome window

3. Keep Chrome open and run this test

═══════════════════════════════════════════════════════════
""")
    
    asyncio.run(test_connection())