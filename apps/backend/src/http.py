"""HTTP session with optional proxy support."""

from aiohttp import ClientSession, ClientTimeout


class ProxySession(ClientSession):
    def __init__(self, proxy_url: str | None = None, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._proxy_url = proxy_url

    async def _request(self, method: str, url: str, **kwargs: object) -> object:
        if self._proxy_url is not None:
            kwargs.setdefault("proxy", self._proxy_url)
        return await super()._request(method, url, **kwargs)
