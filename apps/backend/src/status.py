"""Synthetic uptime checks against the three upstream sources, using known real applications."""

import asyncio
import datetime
import time

from src.logger import logger
from src.models import VisaResult
from src.scrapers.indian_site import fetch_indian
from src.scrapers.passtrack import fetch_passtrack
from src.store import store
from src.tracker import BD_NIC, GOV_IN

DATASET: list[tuple[str, str]] = [
    ("BGDDVC4E9224", "A08143830"),
    ("BGDDV988A224", "A06958329"),
    ("BGDDV8F16C24", "A05137535"),
    ("BGDDVCE50924", "A114944870"),
    ("BGDDVC60A524", "B00022348"),
    ("BGDDVB280A24", "A15691328"),
    ("BGDSV1015024", "A15768078"),
    ("BGDDV9D4CD24", "A04931002"),
    ("BGDRV198C724", "A15208090"),
    ("BGDRV198EC24", "A15208092"),
    ("BGDRV19F3724", "EG0212900"),
    ("BGDRV198D124", "A15208089"),
    ("BGDDVAACCC24", "A07084014"),
    ("BGDDVB174A24", "EH0877306"),
    ("BGDRV1BB5324", "A01765767"),
    ("BGDDVCE59A24", "A01909484"),
    ("BGDDVD242D24", "A03783698"),
]


async def _check(name: str, coro) -> dict:
    t0 = time.monotonic()
    try:
        r: VisaResult = await coro
        latency_ms = round((time.monotonic() - t0) * 1000)
        ok = bool(r.status_text) or bool(r.applicant_name) or bool(r.passtrack)
        return {"ok": ok, "latency_ms": latency_ms, "error": None if ok else "empty result after retries"}
    except Exception as e:
        latency_ms = round((time.monotonic() - t0) * 1000)
        logger.warning("Status check %s crashed: %s", name, e)
        return {"ok": False, "latency_ms": latency_ms, "error": str(e)[:300]}


async def run_check() -> dict:
    """Rotate through the known-good dataset (one entry per hour) and exercise all 3 scrapers."""
    idx = int(time.time() // 3600) % len(DATASET)
    app_id, passport = DATASET[idx]

    passtrack_r, gov_r, bd_r = await asyncio.gather(
        _check("passtrack", fetch_passtrack(app_id)),
        _check("indian_gov", fetch_indian(GOV_IN, app_id, passport)),
        _check("bd_nic", fetch_indian(BD_NIC, app_id, passport)),
    )

    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc),
        "application_id": app_id,
        "passport_number": passport,
        "passtrack": passtrack_r,
        "indian_gov": gov_r,
        "bd_nic": bd_r,
    }
    await store.save_status_check(record)
    logger.info(
        "Status check complete (%s): passtrack=%s gov=%s bd=%s",
        app_id, passtrack_r["ok"], gov_r["ok"], bd_r["ok"],
    )
    return record
