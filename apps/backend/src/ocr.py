"""OCR solvers — ddddocr (ONNX) primary, 2captcha as cloud fallback."""

import asyncio
import base64

import aiohttp

from src.config import get_settings
from src.logger import logger

_ocr = None


def _get_ocr():
    global _ocr
    if _ocr is None:
        import ddddocr

        _ocr = ddddocr.DdddOcr(show_ad=False)
    return _ocr


def _run_ocr(img_bytes: bytes) -> str:
    """Classify captcha bytes via ddddocr (ONNX — cross-platform, no system deps)."""
    try:
        return _get_ocr().classification(img_bytes)
    except Exception:
        logger.exception("ddddocr failed")
        return ""


async def solve_captcha_async(img_bytes: bytes) -> str:
    """Run OCR in a thread-pool executor so the event loop stays unblocked."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run_ocr, img_bytes)


async def solve_2captcha(img_bytes: bytes) -> str:
    """Submit a captcha image to 2captcha and poll for the result."""
    key = get_settings().two_captcha_key
    if not key:
        logger.error("two_captcha_key not configured")
        return ""
    b64 = base64.b64encode(img_bytes).decode()
    async with aiohttp.ClientSession() as s:
        async with s.post(
            "https://2captcha.com/in.php",
            data={"key": key, "method": "base64", "body": b64, "json": 1},
        ) as r:
            resp = await r.json(content_type=None)
            if resp.get("status") != 1:
                logger.error("2captcha submit error: %s", resp)
                return ""
            cap_id = resp["request"]

        for _ in range(30):
            await asyncio.sleep(4)
            async with s.get(
                "https://2captcha.com/res.php",
                params={"key": key, "action": "get", "id": cap_id, "json": 1},
            ) as r:
                resp = await r.json(content_type=None)
                if resp.get("status") == 1:
                    result = resp["request"]
                    logger.info("2captcha solved: %s", result)
                    return result
                if resp.get("request") != "CAPCHA_NOT_READY":
                    logger.error("2captcha poll error: %s", resp)
                    return ""
    logger.warning("2captcha timed out after 120s")
    return ""
