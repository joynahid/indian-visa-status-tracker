"""Optimistic proxy provider — try and learn."""

import asyncio
import random

from src.config import get_settings
from src.logger import logger


class ProxyProvider:
    def __init__(self, urls: list[str]) -> None:
        self.all = [u.strip() for u in urls if u.strip()]
        self.good: list[str] = []
        self.bad: set[str] = set()
        self._lock = asyncio.Lock()

    async def get(self) -> str | None:
        async with self._lock:
            pool = self.good or [p for p in self.all if p not in self.bad]
            if not pool:
                self.bad.clear()
                pool = self.all
            return random.choice(pool) if pool else None

    async def report_bad(self, url: str) -> None:
        async with self._lock:
            self.bad.add(url)
            if url in self.good:
                self.good.remove(url)
                logger.info("Proxy down: %s (%d good left)", url.rsplit("@", 1)[-1], len(self.good))

    async def report_good(self, url: str) -> None:
        async with self._lock:
            if url not in self.good and url in self.all:
                self.good.append(url)
                self.bad.discard(url)
                logger.info("Proxy up: %s (%d total)", url.rsplit("@", 1)[-1], len(self.good))


_provider: ProxyProvider | None = None


async def get_proxy_provider() -> ProxyProvider:
    global _provider
    if _provider is None:
        urls = get_settings().comma_separated_proxy_urls.split(",")
        _provider = ProxyProvider(urls)
        if _provider.all:
            logger.info("Proxies loaded: %d", len(_provider.all))
    return _provider
