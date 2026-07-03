"""In-memory store for inquiries and results."""

from src.models import Inquiry, StoredRetrieval, WeblogEntry
from src.logger import logger
import shortuuid


class MemoryStore:
    def __init__(self) -> None:
        self._inquiries: dict[str, Inquiry] = {}
        self._retrievals: dict[str, StoredRetrieval] = {}
        self._webfiles: dict[str, WeblogEntry] = {}

    async def create_inquiry(self, app_id: str, passport: str, ip: str | None) -> Inquiry:
        slug = shortuuid.uuid()
        inquiry = Inquiry(slug=slug, application_id=app_id, passport_number=passport, ipaddress=ip)
        self._inquiries[slug] = inquiry
        logger.info(f"Created inquiry {slug}")
        return inquiry

    async def get_inquiry(self, slug: str) -> Inquiry | None:
        return self._inquiries.get(slug)

    async def save_retrieval(self, slug: str, data: StoredRetrieval) -> None:
        self._retrievals[slug] = data

    async def get_retrieval(self, slug: str) -> StoredRetrieval | None:
        return self._retrievals.get(slug)

    async def save_webfile(self, info: WeblogEntry) -> None:
        self._webfiles[info.webfile_id] = info

    async def get_webfile(self, webfile_id: str) -> WeblogEntry | None:
        return self._webfiles.get(webfile_id)


store = MemoryStore()
