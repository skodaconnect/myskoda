"""Models for responses of v1/vehicle-information/{vin}/software-version/update-status endpoint."""

from dataclasses import dataclass, field
from datetime import datetime

from mashumaro import field_options

from .common import BaseResponse, CaseInsensitiveStrEnum


class SoftwareStatus(CaseInsensitiveStrEnum):
    UPDATE_SUCCESSFUL = "UPDATE_SUCCESSFUL"


@dataclass
class SoftwareUpdateStatus(BaseResponse):
    status: SoftwareStatus
    current_software_version: str = field(metadata=field_options(alias="currentSoftwareVersion"))
    car_captured_timestamp: datetime | None = field(
        default=None, metadata=field_options(alias="carCapturedTimestamp")
    )
    release_notes_url: str | None = field(
        default=None, metadata=field_options(alias="releaseNotesUrl")
    )


class UnexpectedSoftwareUpdateStatusError(Exception):
    pass
