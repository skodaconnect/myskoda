"""Models for responses of api/v3/vehicle-maintenance/vehicles/{vin} endpoint."""

from datetime import datetime, time
from enum import StrEnum

from pydantic import BaseModel, Field

from .common import Address, Coordinates, Weekday


class MaintenanceReport(BaseModel):
    captured_at: datetime = Field(None, alias="capturedAt")
    inspection_due_in_days: int = Field(None, alias="inspectionDueInDays")
    inspection_due_in_km: int = Field(None, alias="inspectionDueInKm")
    mileage_in_km: int = Field(None, alias="mileageInKm")
    oil_service_due_in_days: int = Field(None, alias="oilServiceDueInDays")
    oil_service_due_in_km: int = Field(None, alias="oilServiceDueInKm")


class Contact(BaseModel):
    email: str
    phone: str
    url: str


class TimeRange(BaseModel):
    start: time = Field(None, alias="from")
    end: time = Field(None, alias="to")


class OpeningHoursPeriod(BaseModel):
    opening_times: list[TimeRange] = Field(None, alias="openingTimes")
    period_end: Weekday = Field(None, alias="periodEnd")
    period_start: Weekday = Field(None, alias="periodStart")


class CommunicationChannel(StrEnum):
    email = "EMAIL"


class PredictiveMaintenanceSettings(BaseModel):
    email: str
    phone: str
    preferred_channel: CommunicationChannel = Field(None, alias="preferredChannel")
    service_activated: bool = Field(None, alias="serviceActivated")


class PredictiveMaintenance(BaseModel):
    setting: PredictiveMaintenanceSettings


class ServicePartner(BaseModel):
    address: Address
    brand: str
    contact: Contact
    id: str
    location: Coordinates
    name: str
    opening_hours: list[OpeningHoursPeriod] = Field(None, alias="openingHours")
    partner_number: str = Field(None, alias="partnerNumber")


class Maintenance(BaseModel):
    maintenance_report: MaintenanceReport = Field(None, alias="maintenanceReport")
    predictive_maintenance: PredictiveMaintenance | None = Field(
        None, alias="predictiveMaintenance"
    )
    preferred_service_partner: ServicePartner = Field(None, alias="preferredServicePartner")
