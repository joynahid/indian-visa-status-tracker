"""Firestore-backed store for inquiries and results."""

import dataclasses

import shortuuid
from google.cloud.firestore import AsyncClient

from src.config import get_settings
from src.logger import logger
from src.models import Inquiry, StoredRetrieval, WeblogEntry


class FirestoreStore:
    def __init__(self) -> None:
        settings = get_settings()
        self._db = AsyncClient(
            project=settings.firestore_project, database=settings.firestore_database
        )
        self._inquiries = self._db.collection("inquiries")
        self._retrievals = self._db.collection("retrievals")
        self._webfiles = self._db.collection("webfiles")
        self._status_checks = self._db.collection("status_checks")

    async def create_inquiry(self, app_id: str, passport: str, ip: str | None) -> Inquiry:
        slug = shortuuid.uuid()
        inquiry = Inquiry(slug=slug, application_id=app_id, passport_number=passport, ipaddress=ip)
        await self._inquiries.document(slug).set(dataclasses.asdict(inquiry))
        logger.info(f"Created inquiry {slug}")
        return inquiry

    async def get_inquiry(self, slug: str) -> Inquiry | None:
        doc = await self._inquiries.document(slug).get()
        if not doc.exists:
            return None
        return Inquiry(**doc.to_dict())

    async def save_retrieval(self, slug: str, data: StoredRetrieval) -> None:
        await self._retrievals.document(slug).set(dataclasses.asdict(data))

    async def merge_retrieval(self, slug: str, **fields: object) -> None:
        """Atomically merge fields into a retrieval doc without a read-modify-write."""
        await self._retrievals.document(slug).set(fields, merge=True)

    async def get_retrieval(self, slug: str) -> StoredRetrieval | None:
        doc = await self._retrievals.document(slug).get()
        if not doc.exists:
            return None
        return StoredRetrieval(**doc.to_dict())

    async def save_webfile(self, info: WeblogEntry) -> None:
        await self._webfiles.document(info.webfile_id).set(dataclasses.asdict(info))

    async def get_webfile(self, webfile_id: str) -> WeblogEntry | None:
        doc = await self._webfiles.document(webfile_id).get()
        if not doc.exists:
            return None
        return WeblogEntry(**doc.to_dict())

    async def save_status_check(self, record: dict) -> None:
        await self._status_checks.add(record)

    async def get_recent_status_checks(self, limit: int = 100) -> list[dict]:
        query = self._status_checks.order_by("timestamp", direction="DESCENDING").limit(limit)
        return [doc.to_dict() async for doc in query.stream()]


store = FirestoreStore()
