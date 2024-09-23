"""Models for responses of api/v3/vehicle-maintenance/vehicles/{vin} endpoint."""

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.json import DataClassJSONMixin

from .common import Address, Coordinates, Weekday


@dataclass
class MaintenanceReport(DataClassJSONMixin):
    captured_at: datetime = field(metadata=field_options(alias="capturedAt"))
    inspection_due_in_days: int = field(metadata=field_options(alias="inspectionDueInDays"))
    mileage_in_km: int = field(metadata=field_options(alias="mileageInKm"))
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
class Contact(DataClassJSONMixin):
    email: str | None = field(default=None)
    phone: str | None = field(default=None)
    url: str | None = field(default=None)


@dataclass
class TimeRange(DataClassJSONMixin):
    start: time = field(metadata=field_options(alias="from"))
    end: time = field(metadata=field_options(alias="to"))


@dataclass
class OpeningHoursPeriod(DataClassJSONMixin):
    opening_times: list[TimeRange] = field(metadata=field_options(alias="openingTimes"))
    period_end: Weekday = field(metadata=field_options(alias="periodEnd"))
    period_start: Weekday = field(metadata=field_options(alias="periodStart"))


class CommunicationChannel(StrEnum):
    email = "EMAIL"


@dataclass
class PredictiveMaintenanceSettings(DataClassJSONMixin):
    email: str
    phone: str
    preferred_channel: CommunicationChannel = field(
        metadata=field_options(alias="preferredChannel")
    )
    service_activated: bool = field(metadata=field_options(alias="serviceActivated"))


@dataclass
class PredictiveMaintenance(DataClassJSONMixin):
    setting: PredictiveMaintenanceSettings


@dataclass
class ServicePartner(DataClassJSONMixin):
    address: Address
    brand: str
    contact: Contact
    id: str
    location: Coordinates
    name: str
    opening_hours: list[OpeningHoursPeriod] = field(metadata=field_options(alias="openingHours"))
    partner_number: str = field(metadata=field_options(alias="partnerNumber"))


@dataclass
class Maintenance(DataClassJSONMixin):
    maintenance_report: MaintenanceReport = field(metadata=field_options(alias="maintenanceReport"))
    predictive_maintenance: PredictiveMaintenance | None = field(
        default=None, metadata=field_options(alias="predictiveMaintenance")
    )
    preferred_service_partner: ServicePartner | None = field(
        default=None, metadata=field_options(alias="preferredServicePartner")
    )
