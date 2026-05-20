"""Models for charging history API responses."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import BaseResponse


def _parse_local_datetime(value: str | None) -> datetime | None:
    """Parse a user-local formatted datetime string (dd.MM.yy HH:mm) as a naive datetime."""
    if value is None:
        return None
    return datetime.strptime(value, "%d.%m.%y %H:%M")  # noqa: DTZ007


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
    id: str


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
    is_active_sessions_enabled: bool = field(
        default=True, metadata=field_options(alias="isActiveSessionsEnabled")
    )
    is_export_enabled: bool = field(default=True, metadata=field_options(alias="isExportEnabled"))


# Response models for the new POST /charging_statistics endpoint


@dataclass
class ChargingStatisticsSessionDetails(DataClassORJSONMixin):
    session_id: UUID = field(metadata=field_options(alias="sessionId"))
    charging_power_type: ChargingCurrentType = field(
        metadata=field_options(alias="chargingPowerType")
    )
    is_active_session: bool = field(metadata=field_options(alias="isActiveSession"))
    formatted_total_energy: str | None = field(
        default=None, metadata=field_options(alias="formattedTotalEnergy")
    )
    # Timestamps are in user-local time (no UTC offset); stored as naive datetimes.
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


@dataclass
class ChargingStatisticsSection(DataClassORJSONMixin):
    title: str
    entries: list[ChargingStatisticsEntry] = field(default_factory=list)


@dataclass
class ChargingStatistics(DataClassORJSONMixin):
    month_sections: list[ChargingStatisticsSection] = field(
        default_factory=list, metadata=field_options(alias="monthSections")
    )
    csv_file: str | None = field(default=None, metadata=field_options(alias="csvFile"))
