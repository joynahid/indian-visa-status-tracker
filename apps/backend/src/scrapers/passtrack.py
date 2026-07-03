"""Passtrack.net scraper."""

import asyncio
import random

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup

from src.logger import logger
from src.models import VisaResult
from src.ocr import solve_captcha_async, solve_2captcha

BASE = "https://www.passtrack.net"

_session: aiohttp.ClientSession | None = None


def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
        )
    return _session


async def close_session() -> None:
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None


class Passtrack:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session
        self.captcha = f"{BASE}/captcha.php?{random.random()}"
        self.form = f"{BASE}/regular_passport.php"

    async def _grab_captcha(self) -> bytes | None:
        async with self.session.get(self.captcha) as r:
            if r.status != 200:
                return None
            return await r.read()

    async def _submit(self, appref: str, code: str) -> str | None:
        d = aiohttp.FormData()
        d.add_field("appref1", appref)
        d.add_field("captcha", code)
        d.add_field("submit", "Submit")
        async with self.session.post(
            self.form,
            data=d,
            headers={"referer": self.form, "origin": BASE},
        ) as r:
            text = await r.text()
            return None if "Plase enter correct code" in text else text

    def _parse(self, html: str) -> tuple[str, dict] | None:
        soup = BeautifulSoup(html, "html.parser")
        name = ""
        # Extract applicant name from any <b> tag
        for b in soup.find_all("b"):
            txt = b.get_text()
            if "Applicant Name :" in txt and b.next_sibling:
                name = str(b.next_sibling).strip()
                break

        # Extract Process/Status from tables (no pandas — direct HTML parsing)
        out: dict = {}
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue
            # Check if this table has the right structure
            process_row = {}
            status_row = {}
            has_data = False
            for tr in rows:
                cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
                if len(cells) < 3:
                    continue
                # Try to find step number
                step_text = cells[0]
                step_num = step_text.replace("Step ", "").strip()
                try:
                    step_key = str(int(step_num) - 1)  # 0-indexed
                except ValueError:
                    continue
                process_row[step_key] = cells[1]
                status_row[step_key] = cells[2]
                has_data = True
            if has_data:
                out["Process"] = process_row
                out["Status"] = status_row
                break

        if not name and not out:
            return None
        return name, out


async def fetch_passtrack(app_id: str, _proxy=None, retries: int = 8) -> VisaResult:
    """Fetch passtrack with generous retries. Auto-heals by resetting session on persistent failures."""
    for attempt in range(retries):
        # Auto-heal: reset session every 3 attempts to clear bad cookies/state
        if attempt > 0 and attempt % 3 == 0:
            logger.info("Passtrack auto-heal: resetting session")
            await close_session()
        p = Passtrack(_get_session())
        cap_bytes = await p._grab_captcha()
        if cap_bytes is None:
            await asyncio.sleep(0.5)
            continue
        # Mix OCR strategies: ddddocr (fast) for early attempts, 2captcha (reliable) after
        if attempt < 2:
            code = await solve_captcha_async(cap_bytes)
        else:
            logger.info("Passtrack using 2captcha attempt %d/%d", attempt + 1, retries)
            code = await solve_2captcha(cap_bytes)
        if not code or len(code) < 4:
            continue
        try:
            text = await p._submit(app_id, code)
        except Exception as e:
            logger.warning("Passtrack submit error attempt %d: %s", attempt + 1, e)
            continue
        if text is None:
            logger.info("Passtrack CAPTCHA wrong on attempt %d/%d", attempt + 1, retries)
            await asyncio.sleep(0.3)
            continue
        parsed = p._parse(text)
        if parsed:
            name, data = parsed
            return VisaResult(applicant_name=name, passtrack=data, url=BASE)
        # Parse failed but no captcha error — page structure changed or blocked
        logger.warning("Passtrack parse failed on attempt %d", attempt + 1)
    return VisaResult(url=BASE)
