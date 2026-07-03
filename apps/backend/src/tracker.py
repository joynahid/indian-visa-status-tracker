"""Visa tracking orchestrator — fans out to all sources with a short-lived result cache."""

import asyncio
import datetime
import time

from src.config import get_settings
from src.logger import logger
from src.models import PassportTrackInput, TrackData, VisaResult
from src.proxy import get_proxy_provider
from src.scrapers.indian_site import fetch_indian
from src.scrapers.passtrack import fetch_passtrack

GOV_IN = "https://indianvisaonline.gov.in"
BD_NIC = "https://indianvisa-bangladesh.nic.in"

# (results, data, cached_at)
_cache: dict[str, tuple[list, TrackData, float]] = {}


def _cache_key(inp: PassportTrackInput) -> str:
    return f"{inp.application_id}:{inp.passport_number}"


def _parse_dt(text: str) -> datetime.datetime | None:
    try:
        return datetime.datetime.strptime(text.split(" On ")[-1], "%Y-%m-%d")
    except (ValueError, IndexError):
        return None


async def track(inp: PassportTrackInput) -> tuple[list[object], TrackData]:
    key = _cache_key(inp)
    ttl = get_settings().track_cache_ttl_seconds
    cached = _cache.get(key)
    if cached:
        results, data, cached_at = cached
        if time.monotonic() - cached_at < ttl:
            logger.info("Cache hit for %s (TTL %ds)", inp.application_id, ttl)
            return results, data

    p = await get_proxy_provider()
    results = await asyncio.gather(
        fetch_passtrack(inp.application_id, p),
        fetch_indian(GOV_IN, inp.application_id, inp.passport_number, p),
        fetch_indian(BD_NIC, inp.application_id, inp.passport_number, p),
        return_exceptions=True,
    )

    pt = results[0] if not isinstance(results[0], Exception) else VisaResult()
    status = (pt.passtrack or {}).get("Status", {})
    process = (pt.passtrack or {}).get("Process", {})

    data = TrackData(
        passtrack_applicant_name=pt.applicant_name,
        passtrack_received_at_center=status.get("0") == "Done",
        passtrack_process_initiated=status.get("1") == "Done",
        passtrack_ready_for_delivery=status.get("2") == "Done",
        passtrack_delivered_from_center_on=_parse_dt(process.get("3", "")),
        indian_gov_status=(
            results[1].status_text if not isinstance(results[1], Exception) else ""
        ),
        bd_nic_status=(
            results[2].status_text if not isinstance(results[2], Exception) else ""
        ),
    )

    result_list = list(results)
    _cache[key] = (result_list, data, time.monotonic())
    logger.info("Tracking complete for %s", inp.application_id)
    return result_list, data
