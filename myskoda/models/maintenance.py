"""Models for responses of api/v3/vehicle-maintenance/vehicles/{vin} endpoint."""

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import Address, Coordinates, Weekday


@dataclass
class MaintenanceReport(DataClassORJSONMixin):
    captured_at: datetime = field(metadata=field_options(alias="capturedAt"))
    inspection_due_in_days: int = field(metadata=field_options(alias="inspectionDueInDays"))
    mileage_in_km: int | None = field(default=None, metadata=field_options(alias="mileageInKm"))
    inspection_due_in_km: int | None = field(
        default=None, metadata=field_options(alias="inspectionDueInKm")
    )
    oil_service_due_in_days: int | None = field(
        default=None, metadata=field_options(alias="oilServiceDueInDays")
    )
    oil_service_due_in_km: int | None = field(
        default=None, metadata=field_options(alias="oilServiceDueInKm")
    )


@dataclass
class Contact(DataClassORJSONMixin):
    email: str | None = field(default=None)
    phone: str | None = field(default=None)
    url: str | None = field(default=None)


@dataclass
class TimeRange(DataClassORJSONMixin):
    start: time = field(metadata=field_options(alias="from"))
    end: time = field(metadata=field_options(alias="to"))


@dataclass
class OpeningHoursPeriod(DataClassORJSONMixin):
    opening_times: list[TimeRange] = field(metadata=field_options(alias="openingTimes"))
    period_end: Weekday = field(metadata=field_options(alias="periodEnd"))
    period_start: Weekday = field(metadata=field_options(alias="periodStart"))


class CommunicationChannel(StrEnum):
    email = "EMAIL"
    phone = "PHONE"


@dataclass
class PredictiveMaintenanceSettings(DataClassORJSONMixin):
    email: str
    service_activated: bool = field(metadata=field_options(alias="serviceActivated"))
    phone: str | None = field(default=None)
    preferred_channel: CommunicationChannel | None = field(
        default=None,
        metadata=field_options(alias="preferredChannel"),
    )


@dataclass
class PredictiveMaintenance(DataClassORJSONMixin):
    setting: PredictiveMaintenanceSettings


@dataclass
class ServicePartner(DataClassORJSONMixin):
    address: Address
    brand: str
    contact: Contact
    id: str
    location: Coordinates
    name: str
    opening_hours: list[OpeningHoursPeriod] = field(metadata=field_options(alias="openingHours"))
    partner_number: str = field(metadata=field_options(alias="partnerNumber"))


@dataclass
class Maintenance(DataClassORJSONMixin):
    maintenance_report: MaintenanceReport | None = field(
        default=None, metadata=field_options(alias="maintenanceReport")
    )
    predictive_maintenance: PredictiveMaintenance | None = field(
        default=None, metadata=field_options(alias="predictiveMaintenance")
    )
    preferred_service_partner: ServicePartner | None = field(
        default=None, metadata=field_options(alias="preferredServicePartner")
    )
