"""FastAPI route handlers — streaming track."""

import asyncio
import datetime
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from src.config import get_settings
from src.logger import logger
from src.models import PassportTrackInput, StoredRetrieval, WeblogEntry
from src.proxy import ProxyProvider, get_proxy_provider
from src.scrapers.ivac import fetch_ivac
from src.scrapers.passtrack import fetch_passtrack
from src.scrapers.indian_site import fetch_indian
from src.store import store
from src.tracker import GOV_IN, BD_NIC

router = APIRouter()


class _Response(BaseModel):
    result: list[object]
    processing_time_seconds: float
    slug: str
    data: dict[str, object]


def _get_ip(request: Request) -> str:
    return (
        request.headers.get("do-connecting-ip", "")
        or request.headers.get("x-forwarded-for", "")
        or (request.client.host if request.client else "")
    )


async def _save_partial(slug: str, **kwargs) -> None:
    """Atomically merge whatever partial results we have so far (no read-modify-write race)."""
    await store.merge_retrieval(slug, **kwargs)


def _serialize(retrieval: StoredRetrieval, webfile: WeblogEntry | None) -> dict[str, object]:
    # Extract passtrack Process/Status table from the raw response
    pt_raw = retrieval.passtrack_response or {}
    pt_table = pt_raw.get("passtrack", {}) or {}
    return {
        "result": [
            retrieval.passtrack_response,
            retrieval.indian_side_response,
            retrieval.bangladeshi_side_response,
        ],
        "processing_time_seconds": retrieval.retrieval_time_seconds,
        "data": {
            "passtrack": {
                "applicant_name": retrieval.passtrack_applicant_name,
                "received_at_center": retrieval.passtrack_received_at_center,
                "process_initiated": retrieval.passtrack_process_initiated,
                "ready_for_delivery": retrieval.passtrack_ready_for_delivery,
                "delivered_from_center_on": (
                    (retrieval.passtrack_delivered_from_center_on + datetime.timedelta(hours=6)).strftime("%Y-%m-%d")
                    if retrieval.passtrack_delivered_from_center_on else None
                ),
                "url": "https://www.passtrack.net",
                "processes": pt_table.get("Process", {}),
                "statuses": pt_table.get("Status", {}),
            },
            "indianvisa_bangladesh_status_nic_in": {
                "status": retrieval.indianvisa_bangladesh_nic_in, "url": BD_NIC,
            },
            "indianvisa_online_gov_in": {
                "status": retrieval.indianvisa_online_gov_in, "url": GOV_IN,
            },
            "webfile_info": (
                {
                    "name": webfile.name,
                    "ivac_name": webfile.ivac_name or "",
                    "visa_type": webfile.visa_type or "",
                    "appointment_date": (
                        webfile.appointment_date + datetime.timedelta(hours=6)
                    ).strftime("%Y-%m-%d"),
                }
                if webfile else None
            ),
        },
    }


@router.post("/track/start")
async def track_start(
    data: PassportTrackInput,
    request: Request = None,
) -> dict[str, object]:
    """Start tracking in background. Returns slug immediately for client to poll."""
    inquiry = await store.create_inquiry(
        data.application_id, data.passport_number, _get_ip(request) if request else None
    )
    # Init empty retrieval
    await _save_partial(inquiry.slug)
    # Fire-and-forget background tracking
    asyncio.create_task(_run_tracking(inquiry.slug, data))
    return {"slug": inquiry.slug, "status": "tracking"}


async def _run_tracking(slug: str, data: PassportTrackInput) -> None:
    t0 = time.time()
    logger.info("Background tracking: %s / %s", data.application_id, data.passport_number)

    async def _track_one(name: str, coro) -> None:
        try:
            r = await coro
            if isinstance(r, Exception):
                logger.warning("%s failed: %s", name, r)
                return
            logger.info("%s done", name)
        except Exception as e:
            logger.warning("%s crashed: %s", name, e)

    # Launch all 3 in parallel, save each as it completes
    async def _passtrack() -> None:
        try:
            r = await fetch_passtrack(data.application_id)
            await _save_partial(
                slug,
                passtrack_applicant_name=r.applicant_name or "",
                passtrack_response={
                    "applicant_name": r.applicant_name,
                    "passtrack": r.passtrack,
                    "url": r.url,
                    "status_text": r.status_text,
                },
            )
        except Exception as e:
            logger.warning("Passtrack failed: %s", e)

    async def _gov() -> None:
        try:
            r = await fetch_indian(GOV_IN, data.application_id, data.passport_number)
            await _save_partial(
                slug,
                indianvisa_online_gov_in=r.status_text or "",
                indian_side_response={
                    "applicant_name": r.applicant_name,
                    "passtrack": r.passtrack,
                    "url": r.url,
                    "status_text": r.status_text,
                },
            )
        except Exception as e:
            logger.warning("Gov failed: %s", e)

    async def _bd() -> None:
        try:
            r = await fetch_indian(BD_NIC, data.application_id, data.passport_number)
            await _save_partial(
                slug,
                indianvisa_bangladesh_nic_in=r.status_text or "",
                bangladeshi_side_response={
                    "applicant_name": r.applicant_name,
                    "passtrack": r.passtrack,
                    "url": r.url,
                    "status_text": r.status_text,
                },
            )
        except Exception as e:
            logger.warning("BD failed: %s", e)

    await asyncio.gather(_passtrack(), _gov(), _bd())

    elapsed = time.time() - t0
    await _save_partial(slug, retrieval_time_seconds=elapsed)
    logger.info("Background tracking complete in %.2fs", elapsed)


@router.post("/track")
async def track_passport(
    data: PassportTrackInput,
    proxy: ProxyProvider = Depends(get_proxy_provider),
    request: Request = None,
) -> _Response:
    """Sync version — waits for all 3 sources."""
    t0 = time.time()
    inquiry = await store.create_inquiry(
        data.application_id, data.passport_number, _get_ip(request) if request else None
    )

    passtrack_task = asyncio.create_task(_safe_passtrack(data))
    gov_task = asyncio.create_task(_safe_indian(GOV_IN, data))
    bd_task = asyncio.create_task(_safe_indian(BD_NIC, data))

    passtrack_r = await passtrack_task
    gov_r = await gov_task
    bd_r = await bd_task

    wf: WeblogEntry | None = await store.get_webfile(inquiry.application_id)
    if wf is None:
        try:
            ivac = await asyncio.wait_for(
                fetch_ivac(inquiry.application_id, proxy), timeout=5
            )
            if ivac is not None:
                wf = ivac
                await store.save_webfile(ivac)
        except Exception:
            pass

    elapsed = time.time() - t0

    bd_text = bd_r.status_text if not isinstance(bd_r, Exception) else ""
    gov_text = gov_r.status_text if not isinstance(gov_r, Exception) else ""
    pt_name = passtrack_r.applicant_name if not isinstance(passtrack_r, Exception) else ""

    await store.save_retrieval(
        inquiry.slug,
        StoredRetrieval(
            retrieval_time_seconds=elapsed,
            indianvisa_online_gov_in=gov_text,
            indianvisa_bangladesh_nic_in=bd_text,
            passtrack_applicant_name=pt_name,
            passtrack_received_at_center=False,
            passtrack_process_initiated=False,
            passtrack_ready_for_delivery=False,
            passtrack_delivered_from_center_on=None,
        ),
    )

    return _Response(
        result=[
            passtrack_r if not isinstance(passtrack_r, Exception) else {},
            gov_r if not isinstance(gov_r, Exception) else {},
            bd_r if not isinstance(bd_r, Exception) else {},
        ],
        processing_time_seconds=elapsed,
        slug=inquiry.slug,
        data={
            "passtrack": {
                "applicant_name": pt_name,
                "received_at_center": False,
                "process_initiated": False,
                "ready_for_delivery": False,
                "delivered_from_center_on": None,
                "url": "https://www.passtrack.net",
            },
            "indianvisa_bangladesh_status_nic_in": {
                "status": bd_text, "url": BD_NIC,
            },
            "indianvisa_online_gov_in": {
                "status": gov_text, "url": GOV_IN,
            },
            "webfile_info": None,
        },
    )


async def _safe_passtrack(data: PassportTrackInput):
    try:
        return await fetch_passtrack(data.application_id)
    except Exception as e:
        return e


async def _safe_indian(base: str, data: PassportTrackInput):
    try:
        return await fetch_indian(base, data.application_id, data.passport_number)
    except Exception as e:
        return e


@router.get("/track/{slug}")
async def get_status(slug: str, response: Response) -> dict[str, object]:
    # Personal visa data behind a shareable slug — never let this get indexed.
    response.headers["X-Robots-Tag"] = "noindex"

    inquiry = await store.get_inquiry(slug)
    if not inquiry:
        raise HTTPException(404, "Not found")

    retrieval = await store.get_retrieval(slug)
    if retrieval is None:
        # Still processing — return empty
        return {
            "result": [{}, {}, {}],
            "processing_time_seconds": 0.0,
            "data": {
                "passtrack": {"applicant_name": "", "url": "https://www.passtrack.net"},
                "indianvisa_bangladesh_status_nic_in": {"status": "", "url": BD_NIC},
                "indianvisa_online_gov_in": {"status": "", "url": GOV_IN},
                "webfile_info": None,
                "pending": True,
            },
        }

    wf = await store.get_webfile(inquiry.application_id)
    resp = _serialize(retrieval, wf)
    resp["data"]["pending"] = retrieval.retrieval_time_seconds == 0.0
    return resp
