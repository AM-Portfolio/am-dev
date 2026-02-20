import logging
import asyncio
from typing import Optional
# Requires: poetry add playwright
# and: playwright install
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

logger = logging.getLogger(__name__)

class BrowserTool:
    """
    "The Eyes" - Visual Perception using Playwright.
    """
    async def capture_screenshot(self, url: str, output_path: str = "screenshot.png") -> bool:
        if not HAS_PLAYWRIGHT:
            logger.error("Playwright not installed.")
            return False

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url)
                await page.screenshot(path=output_path)
                await browser.close()
                logger.info(f"Screenshot saved to {output_path}")
                return True
        except Exception as e:
            logger.error(f"Browser error: {e}")
            return False

    async def verify_element(self, url: str, selector: str) -> bool:
        if not HAS_PLAYWRIGHT:
            return False
            
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url)
                # Wait for element
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    exists = True
                except:
                    exists = False
                
                await browser.close()
                return exists
        except Exception as e:
            logger.error(f"Browser error: {e}")
            return False

browser_tool = BrowserTool()
