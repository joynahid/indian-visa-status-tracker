"""Indian visa site scraper — pool of Playwright browsers, fast path."""

import asyncio
import os

from bs4 import BeautifulSoup

from src.config import get_settings
from src.logger import logger
from src.models import VisaResult
from src.ocr import _run_ocr, solve_2captcha

_pw = None
_pool: list = []
_pool_lock = asyncio.Lock()
_POOL_SIZE = int(os.environ.get("BROWSER_POOL_SIZE", "2"))


def _proxy_config():
    urls = get_settings().comma_separated_proxy_urls
    if urls:
        parts = urls.split(",")[0].strip().lstrip("http://").lstrip("https://")
        if "@" in parts:
            creds, host = parts.split("@", 1)
            u = creds.split(":")
            return {"server": f"http://{host}", "username": u[0], "password": u[1] if len(u) > 1 else ""}
        return {"server": f"http://{parts}"}
    return None


async def _launch_one():
    from playwright.async_api import async_playwright
    global _pw
    if _pw is None:
        _pw = await async_playwright().start()
    proxy = _proxy_config()
    kwargs = {
        "headless": True,
        "args": ["--disable-blink-features=AutomationControlled",
                 "--no-sandbox", "--disable-setuid-sandbox",
                 "--disable-gpu", "--disable-dev-shm-usage"],
    }
    if proxy:
        kwargs["proxy"] = proxy
    return await _pw.chromium.launch(**kwargs)


async def _get_browser():
    async with _pool_lock:
        while _pool:
            b = _pool.pop()
            if b and b.is_connected():
                return b
        return await _launch_one()


async def _return_browser(b):
    async with _pool_lock:
        if b and b.is_connected() and len(_pool) < _POOL_SIZE:
            _pool.append(b)
        elif b:
            await b.close()


async def close_browser():
    global _pw
    async with _pool_lock:
        for b in _pool:
            try:
                if b and b.is_connected():
                    await b.close()
            except Exception:
                pass
        _pool.clear()
    if _pw:
        await _pw.stop()
        _pw = None


async def fetch_indian(base: str, app: str, pp: str, _proxy=None) -> VisaResult:
    for attempt in range(5):  # generous retries
        browser = None
        context = None
        try:
            # Auto-heal: force a fresh browser every 3 attempts
            if attempt > 0 and attempt % 3 == 0:
                logger.info("Indian site auto-heal: closing browser pool")
                await close_browser()
            browser = await _get_browser()
            context = await browser.new_context()
            page = await context.new_page()

            # Block ONLY non-captcha images/fonts/ads to speed up page load
            async def route_handler(route):
                if "captcha" in route.request.url.lower():
                    return await route.continue_()
                rt = route.request.resource_type
                if rt in ("image", "font", "media", "stylesheet"):
                    return await route.abort()
                return await route.continue_()
            await page.route("**/*", route_handler)

            captcha_bytes = []
            async def on_resp(resp):
                if resp.request.method == "GET" and "captcha" in resp.url.lower():
                    try:
                        captcha_bytes.append(await resp.body())
                    except Exception:
                        pass
            page.on("response", on_resp)

            await page.goto(f"{base}/visa/StatusEnquiry", wait_until="domcontentloaded",
                            timeout=15000, referer=f"{base}/visa/index.html")
            await page.wait_for_selector('input[name="filerfno"]', timeout=8000)

            if captcha_bytes:
                cap_data = captcha_bytes[0]
            else:
                el = await page.query_selector('img[src*="captcha"]')
                cap_data = await el.screenshot()

            # Try ddddocr first (fast), fall back to 2captcha on retry
            if attempt == 0:
                code = _run_ocr(cap_data)
            else:
                logger.info("Using 2captcha for attempt %d", attempt + 1)
                code = await solve_2captcha(cap_data)

            await page.fill('input[name="filerfno"]', app)
            await page.fill('input[name="passport_number"]', pp)
            await page.fill('input[name="captcha"]', code)

            async with page.expect_navigation(timeout=10000):
                await page.click('input[value="Check Status"]')

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            has_form = soup.find("input", {"name": "filerfno"}) is not None
            err = soup.find("p", class_="error_para")

            if has_form:
                logger.info("Incorrect CAPTCHA attempt %d/3 (OCR returned %s)", attempt + 1, code)
                continue

            text = err.get_text(strip=True) if err else ""
            logger.info("Indian visa result: %s", text)
            # Return browser to pool for reuse
            await _return_browser(browser)
            return VisaResult(url=base, status_text=text)

        except Exception as e:
            logger.error("Indian site fetch failed attempt %d/3: %s", attempt + 1, e)
            # Don't return bad browser to pool
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            continue
        finally:
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

    return VisaResult(url=base)
