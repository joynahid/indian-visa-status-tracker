"""PostgreSQL-backed store for inquiries, results, and status checks."""

from __future__ import annotations

import asyncio
import dataclasses
from datetime import datetime, timezone
from typing import Any

import shortuuid
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from src.config import get_settings
from src.logger import logger
from src.models import Inquiry, StoredRetrieval, WeblogEntry

_DDL = """
CREATE TABLE IF NOT EXISTS inquiries (
    slug TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    passport_number TEXT NOT NULL,
    ipaddress TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS retrievals (
    slug TEXT PRIMARY KEY REFERENCES inquiries(slug) ON DELETE CASCADE,
    retrieval_time_seconds DOUBLE PRECISION NOT NULL DEFAULT 0,
    indianvisa_online_gov_in TEXT NOT NULL DEFAULT '',
    indianvisa_bangladesh_nic_in TEXT NOT NULL DEFAULT '',
    passtrack_applicant_name TEXT NOT NULL DEFAULT '',
    passtrack_received_at_center BOOLEAN NOT NULL DEFAULT FALSE,
    passtrack_process_initiated BOOLEAN NOT NULL DEFAULT FALSE,
    passtrack_ready_for_delivery BOOLEAN NOT NULL DEFAULT FALSE,
    passtrack_delivered_from_center_on TIMESTAMPTZ,
    passtrack_response JSONB NOT NULL DEFAULT '{}'::jsonb,
    indian_side_response JSONB NOT NULL DEFAULT '{}'::jsonb,
    bangladeshi_side_response JSONB NOT NULL DEFAULT '{}'::jsonb,
    proxy TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS webfiles (
    webfile_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    appointment_date TIMESTAMPTZ NOT NULL,
    ivac_name TEXT,
    visa_type TEXT
);

CREATE TABLE IF NOT EXISTS status_checks (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS status_checks_timestamp_idx
    ON status_checks (timestamp DESC);
"""

_RETRIEVAL_COLUMNS = (
    "slug",
    "retrieval_time_seconds",
    "indianvisa_online_gov_in",
    "indianvisa_bangladesh_nic_in",
    "passtrack_applicant_name",
    "passtrack_received_at_center",
    "passtrack_process_initiated",
    "passtrack_ready_for_delivery",
    "passtrack_delivered_from_center_on",
    "passtrack_response",
    "indian_side_response",
    "bangladeshi_side_response",
    "proxy",
)


def _stored_retrieval_defaults() -> StoredRetrieval:
    return StoredRetrieval(
        retrieval_time_seconds=0.0,
        indianvisa_online_gov_in="",
        indianvisa_bangladesh_nic_in="",
        passtrack_applicant_name="",
        passtrack_received_at_center=False,
        passtrack_process_initiated=False,
        passtrack_ready_for_delivery=False,
        passtrack_delivered_from_center_on=None,
    )


def _inquiry_from_row(row: dict[str, Any]) -> Inquiry:
    return Inquiry(
        slug=row["slug"],
        application_id=row["application_id"],
        passport_number=row["passport_number"],
        ipaddress=row["ipaddress"],
    )


def _retrieval_from_row(row: dict[str, Any]) -> StoredRetrieval:
    defaults = _stored_retrieval_defaults()
    return StoredRetrieval(
        retrieval_time_seconds=row["retrieval_time_seconds"] or defaults.retrieval_time_seconds,
        indianvisa_online_gov_in=row["indianvisa_online_gov_in"] or defaults.indianvisa_online_gov_in,
        indianvisa_bangladesh_nic_in=row["indianvisa_bangladesh_nic_in"] or defaults.indianvisa_bangladesh_nic_in,
        passtrack_applicant_name=row["passtrack_applicant_name"] or defaults.passtrack_applicant_name,
        passtrack_received_at_center=(
            row["passtrack_received_at_center"]
            if row["passtrack_received_at_center"] is not None
            else defaults.passtrack_received_at_center
        ),
        passtrack_process_initiated=(
            row["passtrack_process_initiated"]
            if row["passtrack_process_initiated"] is not None
            else defaults.passtrack_process_initiated
        ),
        passtrack_ready_for_delivery=(
            row["passtrack_ready_for_delivery"]
            if row["passtrack_ready_for_delivery"] is not None
            else defaults.passtrack_ready_for_delivery
        ),
        passtrack_delivered_from_center_on=row["passtrack_delivered_from_center_on"],
        passtrack_response=row["passtrack_response"] or {},
        indian_side_response=row["indian_side_response"] or {},
        bangladeshi_side_response=row["bangladeshi_side_response"] or {},
        proxy=row["proxy"],
    )


def _webfile_from_row(row: dict[str, Any]) -> WeblogEntry:
    return WeblogEntry(
        webfile_id=row["webfile_id"],
        name=row["name"],
        appointment_date=row["appointment_date"],
        ivac_name=row["ivac_name"],
        visa_type=row["visa_type"],
    )


def _status_check_from_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row["payload"])
    payload["timestamp"] = row["timestamp"]
    return payload


class PostgresStore:
    def __init__(self) -> None:
        self._pool: AsyncConnectionPool | None = None
        self._init_lock = asyncio.Lock()
        self._ready = False

    async def _get_pool(self) -> AsyncConnectionPool:
        if self._pool is None:
            settings = get_settings()
            if not settings.database_url:
                raise RuntimeError("DATABASE_URL is required")
            self._pool = AsyncConnectionPool(
                settings.database_url,
                min_size=1,
                max_size=5,
                kwargs={"autocommit": True},
            )
            await self._pool.open()
            logger.info("Postgres pool opened")
        return self._pool

    async def _ensure_schema(self) -> None:
        if self._ready:
            return
        async with self._init_lock:
            if self._ready:
                return
            pool = await self._get_pool()
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    for stmt in _DDL.strip().split(";"):
                        sql = stmt.strip()
                        if sql:
                            await cur.execute(f"{sql};")
            self._ready = True
            logger.info("Postgres schema ready")

    async def _fetchone(self, sql: str, params: dict[str, Any]) -> dict[str, Any] | None:
        await self._ensure_schema()
        pool = await self._get_pool()
        async with pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, params)
                return await cur.fetchone()

    async def _fetchall(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        await self._ensure_schema()
        pool = await self._get_pool()
        async with pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
                return list(rows)

    async def _execute(self, sql: str, params: dict[str, Any]) -> None:
        await self._ensure_schema()
        pool = await self._get_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            self._ready = False
            logger.info("Postgres pool closed")

    async def create_inquiry(self, app_id: str, passport: str, ip: str | None) -> Inquiry:
        slug = shortuuid.uuid()
        inquiry = Inquiry(slug=slug, application_id=app_id, passport_number=passport, ipaddress=ip)
        await self._execute(
            """
            INSERT INTO inquiries (slug, application_id, passport_number, ipaddress)
            VALUES (%(slug)s, %(application_id)s, %(passport_number)s, %(ipaddress)s)
            ON CONFLICT (slug) DO UPDATE SET
                application_id = EXCLUDED.application_id,
                passport_number = EXCLUDED.passport_number,
                ipaddress = EXCLUDED.ipaddress
            """,
            dataclasses.asdict(inquiry),
        )
        logger.info("Created inquiry %s", slug)
        return inquiry

    async def ensure_retrieval(self, slug: str) -> None:
        defaults = dataclasses.asdict(_stored_retrieval_defaults())
        defaults["slug"] = slug
        await self._execute(
            """
            INSERT INTO retrievals (
                slug,
                retrieval_time_seconds,
                indianvisa_online_gov_in,
                indianvisa_bangladesh_nic_in,
                passtrack_applicant_name,
                passtrack_received_at_center,
                passtrack_process_initiated,
                passtrack_ready_for_delivery,
                passtrack_delivered_from_center_on,
                passtrack_response,
                indian_side_response,
                bangladeshi_side_response,
                proxy
            ) VALUES (
                %(slug)s,
                %(retrieval_time_seconds)s,
                %(indianvisa_online_gov_in)s,
                %(indianvisa_bangladesh_nic_in)s,
                %(passtrack_applicant_name)s,
                %(passtrack_received_at_center)s,
                %(passtrack_process_initiated)s,
                %(passtrack_ready_for_delivery)s,
                %(passtrack_delivered_from_center_on)s,
                %(passtrack_response)s,
                %(indian_side_response)s,
                %(bangladeshi_side_response)s,
                %(proxy)s
            )
            ON CONFLICT (slug) DO NOTHING
            """,
            {
                **defaults,
                "passtrack_response": Jsonb({}),
                "indian_side_response": Jsonb({}),
                "bangladeshi_side_response": Jsonb({}),
            },
        )

    async def get_inquiry(self, slug: str) -> Inquiry | None:
        row = await self._fetchone(
            """
            SELECT slug, application_id, passport_number, ipaddress
            FROM inquiries
            WHERE slug = %(slug)s
            """,
            {"slug": slug},
        )
        return _inquiry_from_row(row) if row else None

    async def save_retrieval(self, slug: str, data: StoredRetrieval) -> None:
        row = dataclasses.asdict(data)
        row["slug"] = slug
        await self._execute(
            """
            INSERT INTO retrievals (
                slug,
                retrieval_time_seconds,
                indianvisa_online_gov_in,
                indianvisa_bangladesh_nic_in,
                passtrack_applicant_name,
                passtrack_received_at_center,
                passtrack_process_initiated,
                passtrack_ready_for_delivery,
                passtrack_delivered_from_center_on,
                passtrack_response,
                indian_side_response,
                bangladeshi_side_response,
                proxy
            ) VALUES (
                %(slug)s,
                %(retrieval_time_seconds)s,
                %(indianvisa_online_gov_in)s,
                %(indianvisa_bangladesh_nic_in)s,
                %(passtrack_applicant_name)s,
                %(passtrack_received_at_center)s,
                %(passtrack_process_initiated)s,
                %(passtrack_ready_for_delivery)s,
                %(passtrack_delivered_from_center_on)s,
                %(passtrack_response)s,
                %(indian_side_response)s,
                %(bangladeshi_side_response)s,
                %(proxy)s
            )
            ON CONFLICT (slug) DO UPDATE SET
                retrieval_time_seconds = EXCLUDED.retrieval_time_seconds,
                indianvisa_online_gov_in = EXCLUDED.indianvisa_online_gov_in,
                indianvisa_bangladesh_nic_in = EXCLUDED.indianvisa_bangladesh_nic_in,
                passtrack_applicant_name = EXCLUDED.passtrack_applicant_name,
                passtrack_received_at_center = EXCLUDED.passtrack_received_at_center,
                passtrack_process_initiated = EXCLUDED.passtrack_process_initiated,
                passtrack_ready_for_delivery = EXCLUDED.passtrack_ready_for_delivery,
                passtrack_delivered_from_center_on = EXCLUDED.passtrack_delivered_from_center_on,
                passtrack_response = EXCLUDED.passtrack_response,
                indian_side_response = EXCLUDED.indian_side_response,
                bangladeshi_side_response = EXCLUDED.bangladeshi_side_response,
                proxy = EXCLUDED.proxy,
                updated_at = NOW()
            """,
            {
                **row,
                "passtrack_response": Jsonb(row["passtrack_response"] or {}),
                "indian_side_response": Jsonb(row["indian_side_response"] or {}),
                "bangladeshi_side_response": Jsonb(row["bangladeshi_side_response"] or {}),
            },
        )

    async def merge_retrieval(self, slug: str, **fields: object) -> None:
        """Merge a partial retrieval update without clobbering existing values."""
        if not fields:
            return
        column_values: dict[str, object] = {column: None for column in _RETRIEVAL_COLUMNS if column != "slug"}
        for key, value in fields.items():
            if key not in column_values:
                continue
            column_values[key] = value

        params = {"slug": slug, **column_values}
        await self._execute(
            """
            INSERT INTO retrievals (
                slug,
                retrieval_time_seconds,
                indianvisa_online_gov_in,
                indianvisa_bangladesh_nic_in,
                passtrack_applicant_name,
                passtrack_received_at_center,
                passtrack_process_initiated,
                passtrack_ready_for_delivery,
                passtrack_delivered_from_center_on,
                passtrack_response,
                indian_side_response,
                bangladeshi_side_response,
                proxy
            ) VALUES (
                %(slug)s,
                %(retrieval_time_seconds)s,
                %(indianvisa_online_gov_in)s,
                %(indianvisa_bangladesh_nic_in)s,
                %(passtrack_applicant_name)s,
                %(passtrack_received_at_center)s,
                %(passtrack_process_initiated)s,
                %(passtrack_ready_for_delivery)s,
                %(passtrack_delivered_from_center_on)s,
                %(passtrack_response)s,
                %(indian_side_response)s,
                %(bangladeshi_side_response)s,
                %(proxy)s
            )
            ON CONFLICT (slug) DO UPDATE SET
                retrieval_time_seconds = COALESCE(EXCLUDED.retrieval_time_seconds, retrievals.retrieval_time_seconds),
                indianvisa_online_gov_in = COALESCE(EXCLUDED.indianvisa_online_gov_in, retrievals.indianvisa_online_gov_in),
                indianvisa_bangladesh_nic_in = COALESCE(EXCLUDED.indianvisa_bangladesh_nic_in, retrievals.indianvisa_bangladesh_nic_in),
                passtrack_applicant_name = COALESCE(EXCLUDED.passtrack_applicant_name, retrievals.passtrack_applicant_name),
                passtrack_received_at_center = COALESCE(EXCLUDED.passtrack_received_at_center, retrievals.passtrack_received_at_center),
                passtrack_process_initiated = COALESCE(EXCLUDED.passtrack_process_initiated, retrievals.passtrack_process_initiated),
                passtrack_ready_for_delivery = COALESCE(EXCLUDED.passtrack_ready_for_delivery, retrievals.passtrack_ready_for_delivery),
                passtrack_delivered_from_center_on = COALESCE(EXCLUDED.passtrack_delivered_from_center_on, retrievals.passtrack_delivered_from_center_on),
                passtrack_response = COALESCE(EXCLUDED.passtrack_response, retrievals.passtrack_response),
                indian_side_response = COALESCE(EXCLUDED.indian_side_response, retrievals.indian_side_response),
                bangladeshi_side_response = COALESCE(EXCLUDED.bangladeshi_side_response, retrievals.bangladeshi_side_response),
                proxy = COALESCE(EXCLUDED.proxy, retrievals.proxy),
                updated_at = NOW()
            """,
            {
                **params,
                "passtrack_response": Jsonb(fields.get("passtrack_response"))
                if "passtrack_response" in fields and fields.get("passtrack_response") is not None
                else None,
                "indian_side_response": Jsonb(fields.get("indian_side_response"))
                if "indian_side_response" in fields and fields.get("indian_side_response") is not None
                else None,
                "bangladeshi_side_response": Jsonb(fields.get("bangladeshi_side_response"))
                if "bangladeshi_side_response" in fields and fields.get("bangladeshi_side_response") is not None
                else None,
            },
        )

    async def get_retrieval(self, slug: str) -> StoredRetrieval | None:
        row = await self._fetchone(
            """
            SELECT
                slug,
                retrieval_time_seconds,
                indianvisa_online_gov_in,
                indianvisa_bangladesh_nic_in,
                passtrack_applicant_name,
                passtrack_received_at_center,
                passtrack_process_initiated,
                passtrack_ready_for_delivery,
                passtrack_delivered_from_center_on,
                passtrack_response,
                indian_side_response,
                bangladeshi_side_response,
                proxy
            FROM retrievals
            WHERE slug = %(slug)s
            """,
            {"slug": slug},
        )
        return _retrieval_from_row(row) if row else None

    async def save_webfile(self, info: WeblogEntry) -> None:
        await self._execute(
            """
            INSERT INTO webfiles (webfile_id, name, appointment_date, ivac_name, visa_type)
            VALUES (%(webfile_id)s, %(name)s, %(appointment_date)s, %(ivac_name)s, %(visa_type)s)
            ON CONFLICT (webfile_id) DO UPDATE SET
                name = EXCLUDED.name,
                appointment_date = EXCLUDED.appointment_date,
                ivac_name = EXCLUDED.ivac_name,
                visa_type = EXCLUDED.visa_type
            """,
            dataclasses.asdict(info),
        )

    async def get_webfile(self, webfile_id: str) -> WeblogEntry | None:
        row = await self._fetchone(
            """
            SELECT webfile_id, name, appointment_date, ivac_name, visa_type
            FROM webfiles
            WHERE webfile_id = %(webfile_id)s
            """,
            {"webfile_id": webfile_id},
        )
        return _webfile_from_row(row) if row else None

    async def save_status_check(self, record: dict[str, Any]) -> None:
        payload = {k: v for k, v in record.items() if k != "timestamp"}
        timestamp = record.get("timestamp")
        if not isinstance(timestamp, datetime):
            timestamp = datetime.now(timezone.utc)
        await self._execute(
            """
            INSERT INTO status_checks (timestamp, payload)
            VALUES (%(timestamp)s, %(payload)s)
            """,
            {
                "timestamp": timestamp,
                "payload": Jsonb(payload),
            },
        )

    async def get_recent_status_checks(self, limit: int = 100) -> list[dict]:
        rows = await self._fetchall(
            """
            SELECT timestamp, payload
            FROM status_checks
            ORDER BY timestamp DESC
            LIMIT %(limit)s
            """,
            {"limit": limit},
        )
        return [_status_check_from_row(row) for row in rows]


store = PostgresStore()
