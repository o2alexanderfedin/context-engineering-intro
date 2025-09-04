#!/usr/bin/env python3
"""Test the updated LinkedIn login functionality with remembered profiles."""

import asyncio
from src.config import get_settings
from src.linkedin.browser import LinkedInBrowser

async def test_login():
    """Test LinkedIn login with remembered profile handling."""
    settings = get_settings()
    browser = LinkedInBrowser(settings)
    
    try:
        print("Initializing browser...")
        await browser.initialize()
        
        print("Attempting to login to LinkedIn...")
        success = await browser.login(
            email=settings.linkedin_email,
            password=settings.linkedin_password
        )
        
        if success:
            print("✅ Successfully logged in to LinkedIn!")
            print("Testing navigation to jobs page...")
            
            # Try navigating to jobs page to verify login
            if browser.page:
                await browser.page.goto("https://www.linkedin.com/jobs/")
                await asyncio.sleep(3)
                
                # Check if we're on the jobs page
                if "/jobs" in browser.page.url:
                    print("✅ Successfully navigated to jobs page")
                else:
                    print(f"Current URL: {browser.page.url}")
        else:
            print("❌ Login failed")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("Closing browser...")
        await browser.close()

if __name__ == "__main__":
    print("Testing LinkedIn login with remembered profile support...")
    asyncio.run(test_login())