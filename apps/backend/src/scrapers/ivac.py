"""IVAC payment info scraper (Bangladesh side)."""

import aiohttp
from aiohttp import ClientTimeout

from src.http import ProxySession
from src.logger import logger
from src.models import WeblogEntry
from src.proxy import ProxyProvider

_MAX_ATTEMPTS = 3


async def fetch_ivac(webfile_no: str, proxy: ProxyProvider) -> WeblogEntry | None:
    for attempt in range(_MAX_ATTEMPTS):
        url = await proxy.get()
        try:
            async with ProxySession(proxy_url=url, timeout=ClientTimeout(total=10)) as s:
                async with s.get("https://payment.ivacbd.com") as r:
                    if r.status != 200:
                        return None
                    if url:
                        await proxy.report_good(url)
                    return None  # TODO: parse response into WeblogEntry
        except aiohttp.ClientHttpProxyError:
            if url:
                await proxy.report_bad(url)
            logger.warning("IVAC proxy error on attempt %d/%d", attempt + 1, _MAX_ATTEMPTS)
        except Exception:
            logger.exception("IVAC fetch failed")
            return None
    return None
