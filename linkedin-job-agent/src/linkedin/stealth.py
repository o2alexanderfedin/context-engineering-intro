"""Stealth measures for browser automation."""

import random

from playwright.async_api import Page


async def apply_stealth(page: Page) -> None:
    """Apply stealth measures to avoid detection."""

    # Remove webdriver property
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    # Override permissions
    await page.add_init_script("""
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)

    # Fix Chrome object
    await page.add_init_script("""
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
    """)

    # Override plugins
    await page.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5].map(n => ({
                name: `Chrome PDF Plugin ${n}`,
                description: 'Portable Document Format',
                filename: 'internal-pdf-viewer',
                length: 1
            }))
        });
    """)

    # Override language and platform
    await page.add_init_script("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });
    """)

    # Mock media devices
    await page.add_init_script("""
        navigator.mediaDevices.getUserMedia =
        navigator.webkitGetUserMedia =
        navigator.mozGetUserMedia =
        navigator.getUserMedia = () => {
            return new Promise((resolve, reject) => {
                reject(new Error('Not allowed'));
            });
        };
    """)

    # Override WebGL vendor and renderer
    await page.add_init_script("""
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.apply(this, arguments);
        };
    """)

    # Add more realistic window properties
    await page.add_init_script("""
        window.chrome.runtime.id = 'dfhdfhdfhdfhdfh';
        window.chrome.runtime.getManifest = () => ({
            name: 'Google Chrome',
            version: '120.0.0.0'
        });
    """)

    # Override hardwareConcurrency
    await page.add_init_script("""
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
    """)

    # Add battery API
    await page.add_init_script("""
        navigator.getBattery = () => Promise.resolve({
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity,
            level: 0.98,
            onchargingchange: null,
            onchargingtimechange: null,
            ondischargingtimechange: null,
            onlevelchange: null
        });
    """)

    # Override timezone
    await page.add_init_script("""
        Date.prototype.getTimezoneOffset = function() { return -480; };
        Intl.DateTimeFormat.prototype.resolvedOptions = function() {
            return {
                timeZone: 'America/Los_Angeles',
                locale: 'en-US'
            };
        };
    """)


async def add_mouse_movements(page: Page) -> None:
    """Add realistic mouse movements."""
    await page.evaluate("""
        () => {
            let lastX = 0;
            let lastY = 0;

            const moveMouseSmoothly = async (targetX, targetY) => {
                const steps = 20;
                const startX = lastX;
                const startY = lastY;

                for (let i = 0; i <= steps; i++) {
                    const progress = i / steps;
                    const easeProgress = 1 - Math.cos((progress * Math.PI) / 2);

                    const x = startX + (targetX - startX) * easeProgress;
                    const y = startY + (targetY - startY) * easeProgress;

                    const event = new MouseEvent('mousemove', {
                        clientX: x,
                        clientY: y,
                        bubbles: true,
                        cancelable: true
                    });

                    document.dispatchEvent(event);
                    lastX = x;
                    lastY = y;

                    await new Promise(resolve => setTimeout(resolve, 10));
                }
            };

            // Random movements every few seconds
            setInterval(async () => {
                if (Math.random() > 0.3) {
                    const targetX = Math.random() * window.innerWidth;
                    const targetY = Math.random() * window.innerHeight;
                    await moveMouseSmoothly(targetX, targetY);
                }
            }, Math.random() * 5000 + 3000);
        }
    """)


def get_random_viewport() -> dict[str, int]:
    """Get random realistic viewport size."""
    viewports = [
        {"width": 1920, "height": 1080},  # Full HD
        {"width": 1366, "height": 768},   # Common laptop
        {"width": 1440, "height": 900},   # Macbook
        {"width": 1536, "height": 864},   # Surface
        {"width": 1680, "height": 1050},  # Widescreen
        {"width": 2560, "height": 1440},  # QHD
    ]
    return random.choice(viewports)


def get_random_user_agent() -> str:
    """Get random realistic user agent."""
    user_agents = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

        # Chrome on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",

        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    ]
    return random.choice(user_agents)


def get_random_accept_language() -> str:
    """Get random accept language header."""
    languages = [
        "en-US,en;q=0.9",
        "en-US,en;q=0.9,es;q=0.8",
        "en-GB,en;q=0.9,en-US;q=0.8",
        "en-US,en;q=0.9,fr;q=0.8",
        "en-US,en;q=0.9,de;q=0.8",
    ]
    return random.choice(languages)


async def random_scroll(page: Page) -> None:
    """Perform random scrolling on page."""
    await page.evaluate("""
        () => {
            const scrollHeight = document.documentElement.scrollHeight;
            const viewportHeight = window.innerHeight;
            const maxScroll = scrollHeight - viewportHeight;

            if (maxScroll > 0) {
                const scrollTo = Math.random() * maxScroll;
                window.scrollTo({
                    top: scrollTo,
                    behavior: 'smooth'
                });
            }
        }
    """)


async def random_mouse_click(page: Page, x: int, y: int) -> None:
    """Perform mouse click with random variations."""
    # Add small random offset
    offset_x = random.randint(-2, 2)
    offset_y = random.randint(-2, 2)

    # Move to position first
    await page.mouse.move(x + offset_x, y + offset_y, steps=random.randint(5, 10))

    # Small delay
    await page.wait_for_timeout(random.randint(100, 300))

    # Click with random delay
    await page.mouse.down()
    await page.wait_for_timeout(random.randint(50, 150))
    await page.mouse.up()


async def type_with_mistakes(page: Page, selector: str, text: str) -> None:
    """Type text with occasional mistakes and corrections."""
    element = await page.query_selector(selector)
    if not element:
        return

    await element.click()

    for i, char in enumerate(text):
        # Occasionally make a typo
        if random.random() < 0.05 and i > 0:
            wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
            await page.keyboard.type(wrong_char)
            await page.wait_for_timeout(random.randint(100, 300))
            await page.keyboard.press("Backspace")
            await page.wait_for_timeout(random.randint(50, 150))

        # Type the correct character
        await page.keyboard.type(char)

        # Variable typing speed
        if char == " ":
            await page.wait_for_timeout(random.randint(50, 150))
        else:
            await page.wait_for_timeout(random.randint(30, 120))

        # Occasionally pause (thinking)
        if random.random() < 0.05:
            await page.wait_for_timeout(random.randint(500, 1500))
