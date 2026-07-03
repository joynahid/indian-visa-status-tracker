"""Domain models and contracts."""

import datetime
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel


class PassportTrackInput(BaseModel):
    application_id: str
    passport_number: str


@dataclass
class VisaResult:
    applicant_name: str = ""
    passtrack: dict[str, Any] = field(default_factory=dict)
    url: str = ""
    status_text: str | None = None


@dataclass
class TrackData:
    passtrack_applicant_name: str = ""
    passtrack_received_at_center: bool = False
    passtrack_process_initiated: bool = False
    passtrack_ready_for_delivery: bool = False
    passtrack_delivered_from_center_on: datetime.datetime | None = None
    indian_gov_status: str = ""
    bd_nic_status: str = ""


@dataclass
class WeblogEntry:
    webfile_id: str
    name: str
    appointment_date: datetime.datetime
    ivac_name: str | None = None
    visa_type: str | None = None


@dataclass
class Inquiry:
    slug: str
    application_id: str
    passport_number: str
    ipaddress: str | None = None


@dataclass
class StoredRetrieval:
    retrieval_time_seconds: float
    indianvisa_online_gov_in: str
    indianvisa_bangladesh_nic_in: str
    passtrack_applicant_name: str
    passtrack_received_at_center: bool
    passtrack_process_initiated: bool
    passtrack_ready_for_delivery: bool
    passtrack_delivered_from_center_on: datetime.datetime | None
    passtrack_response: dict[str, Any] = field(default_factory=dict)
    indian_side_response: dict[str, Any] = field(default_factory=dict)
    bangladeshi_side_response: dict[str, Any] = field(default_factory=dict)
    proxy: str | None = None
