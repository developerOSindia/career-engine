"""
Browser controller engine using Playwright over Chrome DevTools Protocol (CDP).
Provides human-like mouse movement, realistic typing cadences, and session persistence.
"""
import asyncio
import random
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from core.config_loader import get_config

class BrowserEngine:
    """Manages the remote debugging Chrome browser connection."""
    def __init__(
        self,
        cdp_url: Optional[str] = None,
        min_delay: Optional[float] = None,
        max_delay: Optional[float] = None
    ):
        config = get_config()
        self.cdp_url = cdp_url or config.cdp_url
        self.min_delay = min_delay if min_delay is not None else config.min_delay
        self.max_delay = max_delay if max_delay is not None else config.max_delay
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self) -> Page:
        """Connects to Chrome via CDP or launches Chromium."""
        self.playwright = await async_playwright().start()
        
        try:
            print(f"🔌 Connecting to Chrome session at {self.cdp_url}...")
            from pathlib import Path
            import urllib.request, json

            is_cdp_up = False
            try:
                urllib.request.urlopen(f"{self.cdp_url.rstrip('/')}/json/version", timeout=1.5)
                is_cdp_up = True
            except Exception:
                pass

            if not is_cdp_up:
                print(f"🚀 Chrome CDP port not responding. Auto-launching Chrome with persistent profile...")
                import subprocess
                root = Path(__file__).resolve().parent.parent
                launch_script = root / "launch_chrome.sh"
                if not launch_script.exists():
                    launch_script = root / "scripts" / "launch_chrome.sh"
                subprocess.Popen(["bash", str(launch_script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                for _ in range(10):
                    await asyncio.sleep(1.0)
                    try:
                        urllib.request.urlopen(f"{self.cdp_url.rstrip('/')}/json/version", timeout=1.0)
                        is_cdp_up = True
                        print("✅ Auto-launched Chrome successfully!")
                        break
                    except Exception:
                        pass

            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
            else:
                self.context = await self.browser.new_context()

            # Find existing relevant tab (Naukri, LinkedIn, or clean blank tab)
            pages = self.context.pages
            for p in pages:
                if "naukri.com" in p.url or "linkedin.com" in p.url:
                    self.page = p
                    print(f"📌 Attached to existing tab: {p.url}")
                    break
            
            if not self.page:
                for p in pages:
                    if p.url in ("about:blank", "chrome://newtab/"):
                        self.page = p
                        print(f"📄 Reusing empty browser tab.")
                        break

            if not self.page:
                self.page = await self.context.new_page()
                print("📄 Opened new browser tab.")
                
            return self.page

        except Exception as e:
            print(f"⚠️ CDP connection failed: {e}")
            print("\n💡 TIP: Launch Chrome using './scripts/launch_chrome.sh' in another terminal first, then re-run.")
            raise

    async def check_linkedin_logged_in(self) -> bool:
        """Verifies if the user is authenticated on LinkedIn using the li_at session cookie."""
        if not self.context:
            return False
        try:
            cookies = await self.context.cookies()
            for c in cookies:
                if "linkedin.com" in c.get("domain", "") and c.get("name") == "li_at":
                    return True
            return False
        except Exception:
            return False

    async def random_delay(self, multiplier: float = 1.0):
        """Sleeps for a human-like randomized duration."""
        low = self.min_delay * multiplier
        high = self.max_delay * multiplier
        delay = random.uniform(low, high)
        await asyncio.sleep(delay)

    async def human_click(self, element_or_selector):
        """Hovers and clicks with slight human jitter."""
        if isinstance(element_or_selector, str):
            elem = await self.page.wait_for_selector(element_or_selector, timeout=7000)
        else:
            elem = element_or_selector

        if not elem:
            return False

        await elem.scroll_into_view_if_needed()
        await self.random_delay(0.4)
        await elem.hover()
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await elem.click()
        await self.random_delay(0.6)
        return True

    async def human_type(self, element_or_selector, text: str, clear_first: bool = True):
        """Types text with natural keystroke cadence."""
        if isinstance(element_or_selector, str):
            elem = await self.page.wait_for_selector(element_or_selector, timeout=7000)
        else:
            elem = element_or_selector

        if not elem:
            return False

        await elem.scroll_into_view_if_needed()
        await elem.click()
        if clear_first:
            await self.page.keyboard.press("Meta+A")
            await self.page.keyboard.press("Backspace")
            await asyncio.sleep(0.1)

        for char in str(text):
            await self.page.keyboard.type(char)
            # Randomized typing delay between keystrokes (30ms - 90ms)
            await asyncio.sleep(random.uniform(0.03, 0.09))

        await self.random_delay(0.3)
        return True

    async def close(self):
        """Cleans up browser connections without terminating the user's Chrome process."""
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass
