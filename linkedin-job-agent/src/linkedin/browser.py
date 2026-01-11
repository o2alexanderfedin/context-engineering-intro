"""LinkedIn browser automation using Playwright."""

import asyncio
import json
import random
from pathlib import Path

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from ..config import Settings
from .stealth import apply_stealth


class LinkedInBrowser:
    """Manage LinkedIn browser automation with stealth measures."""

    def __init__(self, settings: Settings):
        """Initialize browser with configuration."""
        self.settings = settings
        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.session_file = Path(".linkedin_session.json")
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    async def initialize(self) -> None:
        """Initialize browser - try to connect to existing session first."""
        self.playwright = await async_playwright().start()

        # First, try to connect to existing Chrome with debugging port
        try:
            # Try to connect to existing browser
            self.browser = await self.playwright.chromium.connect_over_cdp(
                "http://localhost:9222"
            )
            print("✓ Connected to existing Chrome browser")
            
            # Bring Chrome to foreground on macOS
            import subprocess
            import platform
            if platform.system() == "Darwin":  # macOS
                try:
                    subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to activate'], check=False)
                    print("✓ Brought Chrome to foreground")
                except:
                    pass  # Silently ignore if it fails
            
            # Get existing context - reuse the current browser session
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                # Get existing pages or create new one
                pages = self.context.pages
                if pages:
                    # Use existing LinkedIn page if available
                    for page in pages:
                        if "linkedin.com" in page.url:
                            self.page = page
                            print(f"✓ Using existing LinkedIn tab: {page.url}")
                            return
                    # No LinkedIn page, use first available
                    self.page = pages[0]
                else:
                    self.page = await self.context.new_page()
            else:
                # Create new context in existing browser
                await self._create_context()
                self.page = await self.context.new_page()
            
            # Apply minimal stealth to existing session
            await apply_stealth(self.page)
            return
                
        except Exception as e:
            print(f"Could not connect to existing browser: {e}")
            print("Launching new browser instance...")
            print("TIP: To use your existing browser, run:")
            print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
            print()
            
            # Browser launch arguments for stealth
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-setuid-sandbox",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
            ]

            # Add proxy if configured
            proxy = None
            if self.settings.proxy_url:
                proxy = {
                    "server": self.settings.proxy_url,
                    "username": self.settings.proxy_username,
                    "password": self.settings.proxy_password,
                }

            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.settings.headless_mode,
                args=launch_args,
                proxy=proxy,
            )

            # Create context with saved session or new
            await self._create_context()

            # Create page
            self.page = await self.context.new_page()

            # Apply stealth measures
            await apply_stealth(self.page)

            # Add human-like behavior
            await self._add_human_behavior()

    async def _create_context(self) -> None:
        """Create browser context with session management."""
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": random.choice(self.user_agents),
            "locale": "en-US",
            "timezone_id": "America/Los_Angeles",
        }

        # Try to restore session
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    storage_state = json.load(f)
                context_options["storage_state"] = storage_state
            except Exception as e:
                print(f"Failed to restore session: {e}")

        self.context = await self.browser.new_context(**context_options)

    async def _add_human_behavior(self) -> None:
        """Add human-like behavior to browser."""
        if not self.page:
            return

        # Random mouse movements
        await self.page.evaluate("""
            () => {
                let mouseX = 100, mouseY = 100;

                // Listen to real mouse movements
                document.addEventListener('mousemove', (e) => {
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                });

                // Simulate random micro-movements
                setInterval(() => {
                    const jitter = 5;
                    const event = new MouseEvent('mousemove', {
                        clientX: mouseX + (Math.random() - 0.5) * jitter,
                        clientY: mouseY + (Math.random() - 0.5) * jitter,
                        bubbles: true,
                        cancelable: true
                    });
                    document.dispatchEvent(event);
                }, Math.random() * 3000 + 2000);
            }
        """)

        # Random scrolling
        await self.page.evaluate("""
            () => {
                setInterval(() => {
                    const shouldScroll = Math.random() > 0.7;
                    if (shouldScroll) {
                        const scrollAmount = Math.random() * 100 - 50;
                        window.scrollBy({
                            top: scrollAmount,
                            behavior: 'smooth'
                        });
                    }
                }, Math.random() * 5000 + 5000);
            }
        """)

    async def login(self, email: str, password: str) -> bool:
        """Login to LinkedIn."""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        try:
            # First check if we're on a page with a sign-in modal or link
            current_url = self.page.url
            if "linkedin.com" in current_url and "/login" not in current_url:
                # Check for "Sign in to view more jobs" modal
                try:
                    # Look for the modal sign-in button
                    modal_sign_in = await self.page.query_selector("button.sign-in-modal__outlet-btn")
                    if not modal_sign_in:
                        # Also check for the contextual sign-in modal button
                        modal_sign_in = await self.page.query_selector("button[data-modal='base-sign-in-modal']")
                    
                    if modal_sign_in:
                        print("Found sign-in modal button, clicking...")
                        await modal_sign_in.click()
                        await asyncio.sleep(2)
                        
                        # Now look for the email/password fields in the modal
                        email_field = await self.page.query_selector("#base-sign-in-modal_session_key")
                        if email_field:
                            print("Entering credentials in modal...")
                            await self._type_like_human("#base-sign-in-modal_session_key", email)
                            await asyncio.sleep(random.uniform(0.5, 1.0))
                            await self._type_like_human("#base-sign-in-modal_session_password", password)
                            await asyncio.sleep(random.uniform(0.5, 1.0))
                            
                            # Click the sign-in button in the modal
                            modal_submit = await self.page.query_selector("button[data-id='sign-in-form__submit-btn']")
                            if modal_submit:
                                await modal_submit.click()
                                await asyncio.sleep(3)
                                
                                # Check if login was successful
                                current_url = self.page.url
                                if any(path in current_url for path in ["/jobs", "/feed", "/mynetwork"]):
                                    await self.save_session()
                                    return True
                    else:
                        # Try to find regular sign-in link
                        sign_in_link = await self.page.query_selector("a[href*='/login']")
                        if not sign_in_link:
                            sign_in_link = await self.page.query_selector("a:has-text('Sign in')")
                        
                        if sign_in_link:
                            print("Found sign-in link, clicking...")
                            await sign_in_link.click()
                            await self.page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"Modal/link handling: {e}")
                    pass
            
            # Navigate to LinkedIn login if not already there
            if "/login" not in self.page.url:
                await self._smart_goto("https://www.linkedin.com/login", max_wait=5000)

            # Check for remembered profile screen
            try:
                # Check if we're on the remember me page
                remember_div = await self.page.query_selector("#rememberme-div")
                if remember_div:
                    print("Detected remembered profile screen...")
                    
                    # Try to click on the remembered profile
                    profile_button = await self.page.query_selector(".member-profile__details")
                    if profile_button:
                        print("Clicking on remembered profile...")
                        await profile_button.click()
                        await asyncio.sleep(2)
                        
                        # Check if we need to enter password
                        password_field = await self.page.query_selector("#password")
                        if password_field:
                            print("Entering password for remembered profile...")
                            await self._type_like_human("#password", password)
                            await asyncio.sleep(random.uniform(0.5, 1.0))
                            
                            # Submit the form
                            submit_button = await self.page.query_selector("button[type='submit']")
                            if submit_button:
                                await submit_button.click()
                        else:
                            # Already logged in with remembered profile
                            pass
                    else:
                        # Fall back to "Sign in using another account" if no remembered profile
                        other_account = await self.page.query_selector(".signin-other-account")
                        if other_account:
                            print("Clicking 'Sign in using another account'...")
                            await other_account.click()
                            await asyncio.sleep(2)
                            
                            # Now proceed with normal login
                            await self.page.wait_for_selector("#username", timeout=10000)
                            await self._type_like_human("#username", email)
                            await asyncio.sleep(random.uniform(0.5, 1.5))
                            await self._type_like_human("#password", password)
                            await asyncio.sleep(random.uniform(0.5, 1.0))
                            await self.page.click("button[type='submit']")
                else:
                    # Normal login flow
                    await self.page.wait_for_selector("#username", timeout=10000)
                    await self._type_like_human("#username", email)
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    await self._type_like_human("#password", password)
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    await self.page.click("button[type='submit']")
                    
            except Exception as e:
                print(f"Remembered profile handling failed: {e}, trying normal login...")
                # Fall back to normal login
                try:
                    await self.page.wait_for_selector("#username", timeout=10000)
                    await self._type_like_human("#username", email)
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    await self._type_like_human("#password", password)
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    await self.page.click("button[type='submit']")
                except:
                    pass

            # Wait for navigation (handle various scenarios)
            await self.page.goto("https://www.linkedin.com/jobs/collections/recommended/", timeout=30000)
            await self.save_session()
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    async def _smart_goto(self, url: str, max_wait: int = 5000) -> None:
        """Navigate to URL with smart waiting - either networkidle or timeout."""
        if not self.page:
            return
            
        try:
            # Try networkidle with a short timeout
            await self.page.goto(url, wait_until="networkidle", timeout=max_wait)
        except:
            # If networkidle times out, try domcontentloaded
            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=3000)
            except:
                # If even that fails, just wait a bit for the page to load
                await asyncio.sleep(2)
    
    async def _type_like_human(self, selector: str, text: str) -> None:
        """Type text with human-like delays."""
        if not self.page:
            return

        await self.page.click(selector)

        for char in text:
            await self.page.type(selector, char)
            # Random delay between keystrokes (50-150ms)
            await asyncio.sleep(random.uniform(0.05, 0.15))

    async def navigate_to_jobs(self) -> None:
        """Navigate to LinkedIn Jobs section."""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        await self._smart_goto("https://www.linkedin.com/jobs/", max_wait=5000)
        await asyncio.sleep(random.uniform(2, 4))

    async def search_jobs(
        self,
        keywords: str,
        location: str = "",
        remote: bool = False,
    ) -> None:
        """Search for jobs with given criteria."""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        # Use the recommended jobs URL format which works better
        print(f"Navigating to LinkedIn recommended jobs")
        # This URL format shows recommended jobs which is more reliable
        search_url = "https://www.linkedin.com/jobs/collections/recommended/"
        
        # If we want to search with keywords, we can still use the search URL
        if keywords:
            if isinstance(keywords, str):
                keywords_arg = f"keywords={keywords.replace(',', '%2C')}"
            elif isinstance(keywords, list):
                keywords_arg = f"keywords={'%2C'.join(keywords[:10])}"
            else:
                keywords_arg = ""

            search_url = f"https://www.linkedin.com/jobs/search/?{keywords_arg}"
            if location:
                search_url += f"&location={location.replace(',', '%2C')}"

        search_url = search_url.replace(' ', '%20')
        await self._smart_goto(search_url, max_wait=5000)
        await asyncio.sleep(random.uniform(2, 3))
        
        # Don't wait for specific selectors - let AI handle extraction from whatever HTML is present
        print("Page loaded, ready for AI extraction")
        
        # Apply filters if needed
        if remote:
            await self._apply_remote_filter()
        
        return
        
        # Keep original search box code as fallback (but skip for now)
        # Option 1: Try to use search fields if available
        try:
            # Try multiple possible selectors for the search box
            selectors = [
                "input[id*='jobs-search-box-keyword']",
                "input[placeholder*='Search jobs']",
                "input[placeholder*='Search titles']",
                "input[aria-label*='Search']",
                "input.jobs-search-box__text-input",
                "input[id*='global-nav-typeahead']"
            ]
            
            keywords_input = None
            for selector in selectors:
                try:
                    keywords_input = await self.page.wait_for_selector(
                        selector,
                        timeout=2000
                    )
                    if keywords_input:
                        print(f"Found search input with selector: {selector}")
                        break
                except:
                    continue
            
            if not keywords_input:
                # Option 2: Navigate directly to search results URL
                print("Could not find search input, navigating directly to search results...")
                search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}"
                if location:
                    search_url += f"&location={location.replace(' ', '%20').replace(',', '%2C')}"
                
                await self._smart_goto(search_url, max_wait=5000)
                await asyncio.sleep(random.uniform(2, 3))
                return  # Exit early since we navigated directly
            await keywords_input.click(click_count=3)
            await keywords_input.press("Backspace")
            await keywords_input.fill("")  # Clear it first
            await keywords_input.type(keywords)  # Type the keywords

            await asyncio.sleep(random.uniform(0.5, 1.0))

            # Location
            if location:
                location_selectors = [
                    "input[id*='jobs-search-box-location']",
                    "input[placeholder*='Location']",
                    "input[aria-label*='Location']",
                    "input.jobs-search-box__text-input[id*='location']"
                ]
                
                location_input = None
                for selector in location_selectors:
                    try:
                        location_input = await self.page.wait_for_selector(
                            selector,
                            timeout=5000
                        )
                        if location_input:
                            break
                    except:
                        continue
                
                if location_input:
                    await location_input.click(click_count=3)
                    await location_input.press("Backspace")
                    await location_input.fill("")  # Clear it first
                    await location_input.type(location)

            await asyncio.sleep(random.uniform(0.5, 1.0))

            # Click search - try Enter key or search button
            try:
                # First try pressing Enter
                if keywords_input:
                    await keywords_input.press("Enter")
            except:
                # Try clicking search button
                search_button = await self.page.query_selector("button[type='submit']")
                if search_button:
                    await search_button.click()

            # Wait for results with multiple possible selectors
            result_selectors = [
                "ul.jobs-search-results__list",
                "div.jobs-search-results",
                "div[data-job-id]",
                "li.job-card-container"
            ]
            
            for selector in result_selectors:
                try:
                    await self.page.wait_for_selector(
                        selector,
                        timeout=10000
                    )
                    break
                except:
                    continue

            await asyncio.sleep(random.uniform(2, 4))

            # Apply filters
            if remote:
                await self._apply_remote_filter()

        except Exception as e:
            print(f"Search failed: {e}")
            raise

    async def _apply_remote_filter(self) -> None:
        """Apply remote work filter."""
        if not self.page:
            return

        try:
            # Click on filters button
            filters_button = await self.page.query_selector("button:has-text('All filters')")
            if filters_button:
                await filters_button.click()
                await asyncio.sleep(random.uniform(1, 2))

                # Look for remote option
                remote_option = await self.page.query_selector("label:has-text('Remote')")
                if remote_option:
                    await remote_option.click()
                    await asyncio.sleep(random.uniform(0.5, 1))

                    # Apply filters
                    apply_button = await self.page.query_selector("button:has-text('Show results')")
                    if apply_button:
                        await apply_button.click()
                        await asyncio.sleep(random.uniform(2, 3))

        except Exception as e:
            print(f"Failed to apply remote filter: {e}")

    async def save_session(self) -> None:
        """Save browser session for reuse."""
        if not self.context:
            return

        try:
            storage_state = await self.context.storage_state()
            with open(self.session_file, "w") as f:
                json.dump(storage_state, f)
        except Exception as e:
            print(f"Failed to save session: {e}")

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def check_logged_in(self) -> bool:
        """Check if currently logged in to LinkedIn."""
        if not self.page:
            return False

        try:
            current_url = self.page.url
            
            # If already on LinkedIn, just check current page
            if "linkedin.com" in current_url:
                # Check if on logged-in pages
                if any(path in current_url for path in ["/feed", "/mynetwork", "/jobs", "/messaging", "/in/"]):
                    return True
                # Check if on login page
                if "/login" in current_url or "/checkpoint" in current_url:
                    return False
            
            # Navigate to feed to check login status
            await self._smart_goto("https://www.linkedin.com/jobs/collections/recommended/", max_wait=5000)

            # Check for login redirect
            if "/login" in self.page.url or "/checkpoint" in self.page.url:
                return False

            # Check for feed elements or navigation
            selectors = [
                "div.global-nav__content",
                "nav[aria-label='Primary Navigation']",
                "div#global-nav",
                "div.feed-shared-update-v2"
            ]
            
            for selector in selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        return True
                except:
                    continue
            
            return False

        except Exception as e:
            print(f"Error checking login status: {e}")
            return False

    async def handle_rate_limit(self) -> None:
        """Handle rate limiting by waiting."""
        wait_time = random.uniform(30, 60)
        print(f"Rate limit detected. Waiting {wait_time:.0f} seconds...")
        await asyncio.sleep(wait_time)

    async def random_delay(self, min_seconds: float = 1, max_seconds: float = 3) -> None:
        """Add random delay to mimic human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
