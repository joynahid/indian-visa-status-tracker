"""Status page endpoints — synthetic uptime checks against upstream sources."""

from fastapi import APIRouter, Header, HTTPException

from src.config import get_settings
from src.status import run_check
from src.store import store

router = APIRouter(prefix="/status")

SOURCES = ["passtrack", "indian_gov", "bd_nic"]


def _jsonable(record: dict) -> dict:
    r = dict(record)
    ts = r.get("timestamp")
    if hasattr(ts, "isoformat"):
        r["timestamp"] = ts.isoformat()
    return r


@router.post("/run")
async def trigger_check(x_status_secret: str | None = Header(default=None)) -> dict:
    """Triggered by Cloud Scheduler on a cron. Requires a shared secret header."""
    secret = get_settings().status_check_secret
    if not secret or x_status_secret != secret:
        raise HTTPException(403, "Forbidden")
    record = await run_check()
    return {"ok": True, "record": _jsonable(record)}


@router.get("/summary")
async def summary() -> dict:
    checks = await store.get_recent_status_checks(limit=100)
    sources: dict[str, dict] = {}
    for src in SOURCES:
        relevant = [c for c in checks if src in c]
        latest = relevant[0] if relevant else None
        up_count = sum(1 for c in relevant if c[src]["ok"])
        sources[src] = {
            "up": latest[src]["ok"] if latest else None,
            "last_checked": latest["timestamp"].isoformat() if latest else None,
            "latency_ms": latest[src]["latency_ms"] if latest else None,
            "error": latest[src]["error"] if latest else None,
            "uptime_percent": round(100 * up_count / len(relevant), 1) if relevant else None,
            "sample_size": len(relevant),
        }
    return {
        "sources": sources,
        "recent": [_jsonable(c) for c in checks[:20]],
    }
