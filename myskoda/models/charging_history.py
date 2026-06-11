"""Models for charging history API responses."""

import base64
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID

from mashumaro import field_options
from mashumaro.config import (
    TO_DICT_ADD_BY_ALIAS_FLAG,
    TO_DICT_ADD_OMIT_NONE_FLAG,
    BaseConfig,
    CodeGenerationOption,
)
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import BaseResponse, Vin

EMPTY_LOCAL_DATETIME_PLACEHOLDER = "--"


def _parse_local_datetime(value: str | None) -> datetime | None:
    """Parse charging statistics datetime values as UTC."""
    if value is None or value == EMPTY_LOCAL_DATETIME_PLACEHOLDER:
        return None

    for fmt in (
        "%d/%m/%Y, %H:%M",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue

    return datetime.fromisoformat(value).astimezone(UTC)


class ChargingCurrentType(StrEnum):
    AC = "AC"
    DC = "DC"


@dataclass
class ChargingSession(DataClassORJSONMixin):
    start_at: datetime = field(metadata=field_options(alias="startAt"))
    charged_in_kwh: float = field(metadata=field_options(alias="chargedInKWh"))
    duration_in_minutes: int = field(metadata=field_options(alias="durationInMinutes"))
    current_type: ChargingCurrentType = field(metadata=field_options(alias="currentType"))


@dataclass
class ChargingPeriod(DataClassORJSONMixin):
    total_charged_in_kwh: float = field(
        default=0.0, metadata=field_options(alias="totalChargedInKWh")
    )
    sessions: list[ChargingSession] = field(default_factory=list)


@dataclass
class ChargingHistory(BaseResponse):
    next_cursor: datetime | None = field(default=None, metadata=field_options(alias="nextCursor"))
    periods: list[ChargingPeriod] = field(default_factory=list)


# Request models for the new POST /charging_statistics endpoint


@dataclass
class ChargingStatisticsFilterOption(DataClassORJSONMixin):
    filter_type: str = field(metadata=field_options(alias="filterType"))
    vin: Vin | None = None

    class Config(BaseConfig):
        """Configuration for serialization and deserialization."""

        code_generation_options: list[CodeGenerationOption] = [  # noqa: RUF012
            TO_DICT_ADD_BY_ALIAS_FLAG,
            TO_DICT_ADD_OMIT_NONE_FLAG,
        ]


@dataclass
class ChargingStatisticsRequest(DataClassORJSONMixin):
    started_after: date = field(metadata=field_options(alias="startedAfter"))
    started_before: date = field(metadata=field_options(alias="startedBefore"))
    selected_filter_options: list[ChargingStatisticsFilterOption] = field(
        default_factory=list, metadata=field_options(alias="selectedFilterOptions")
    )
    capabilities: list[str] = field(default_factory=list)
    fetch_filter_options: bool = field(
        default=True, metadata=field_options(alias="fetchFilterOptions")
    )
    is_active_sessions_enabled: bool | None = field(
        default=None, metadata=field_options(alias="isActiveSessionsEnabled")
    )
    is_export_enabled: bool | None = field(
        default=None, metadata=field_options(alias="isExportEnabled")
    )

    class Config(BaseConfig):
        """Configuration for serialization and deserialization."""

        code_generation_options: list[CodeGenerationOption] = [  # noqa: RUF012
            TO_DICT_ADD_BY_ALIAS_FLAG,
            TO_DICT_ADD_OMIT_NONE_FLAG,
        ]


@dataclass
class ChargingStatisticsSessionDetails(DataClassORJSONMixin):
    session_id: UUID = field(metadata=field_options(alias="sessionId"))
    charging_power_type: ChargingCurrentType = field(
        metadata=field_options(alias="chargingPowerType")
    )
    is_active_session: bool | None = field(
        default=None, metadata=field_options(alias="isActiveSession")
    )
    is_curve_available: bool | None = field(
        default=None, metadata=field_options(alias="isCurveAvailable")
    )
    formatted_total_energy: str | None = field(
        default=None, metadata=field_options(alias="formattedTotalEnergy")
    )
    charging_start_time: datetime | None = field(
        default=None,
        metadata=field_options(
            alias="formattedChargingStartTime", deserialize=_parse_local_datetime
        ),
    )
    charging_end_time: datetime | None = field(
        default=None,
        metadata=field_options(alias="formattedChargingEndTime", deserialize=_parse_local_datetime),
    )
    formatted_total_charging_time: str | None = field(
        default=None, metadata=field_options(alias="formattedTotalChargingTime")
    )
    formatted_active_charging_time: str | None = field(
        default=None, metadata=field_options(alias="formattedActiveChargingTime")
    )
    formatted_start_soc: str | None = field(
        default=None, metadata=field_options(alias="formattedStartSoc")
    )
    formatted_end_soc: str | None = field(
        default=None, metadata=field_options(alias="formattedEndSoc")
    )


@dataclass
class ChargingStatisticsEntry(DataClassORJSONMixin):
    details: ChargingStatisticsSessionDetails
    id: str | None = None
    title: str | None = None
    primary_value: str | None = field(default=None, metadata=field_options(alias="primaryValue"))
    secondary_value: str | None = field(
        default=None, metadata=field_options(alias="secondaryValue")
    )


@dataclass
class ChargingStatisticsSection(DataClassORJSONMixin):
    title: str
    entries: list[ChargingStatisticsEntry] = field(default_factory=list)


@dataclass
class ChargingStatisticsApplicableFilterOption(DataClassORJSONMixin):
    filter_type: str | None = field(default=None, metadata=field_options(alias="filterType"))
    id: str | None = None
    label: str | None = None


@dataclass
class ChargingStatistics(DataClassORJSONMixin):
    applicable_filter_options: list[ChargingStatisticsApplicableFilterOption] = field(
        default_factory=list, metadata=field_options(alias="applicableFilterOptions")
    )
    month_sections: list[ChargingStatisticsSection] = field(
        default_factory=list, metadata=field_options(alias="monthSections")
    )
    missing_elli_consent: bool | None = field(
        default=None, metadata=field_options(alias="missingElliConsent")
    )
    csv_file: str | None = field(default=None, metadata=field_options(alias="csvFile"))

    @property
    def csv_bytes(self) -> bytes | None:
        """Return the decoded CSV file as bytes."""
        if not self.csv_file:
            return None

        try:
            return base64.b64decode(self.csv_file)
        except ValueError:
            return None

    @property
    def csv_text(self) -> str | None:
        """Return the decoded CSV file as text."""
        data = self.csv_bytes

        if data is None:
            return None

        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace")
