"""Models for responses of api/v2/garage/vehicles/{vin}."""

import logging
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, validator

_LOGGER = logging.getLogger(__name__)


class CapabilityId(StrEnum):
    AIR_CONDITIONING = "AIR_CONDITIONING"
    AIR_CONDITIONING_SAVE_AND_ACTIVATE = "AIR_CONDITIONING_SAVE_AND_ACTIVATE"
    AIR_CONDITIONING_SMART_SETTINGS = "AIR_CONDITIONING_SMART_SETTINGS"
    AIR_CONDITIONING_TIMERS = "AIR_CONDITIONING_TIMERS"
    AUTOMATION = "AUTOMATION"
    BATTERY_CHARGING_CARE = "BATTERY_CHARGING_CARE"
    BATTERY_SUPPORT = "BATTERY_SUPPORT"
    CARE_AND_INSURANCE = "CARE_AND_INSURANCE"
    CHARGE_MODE_SELECTION = "CHARGE_MODE_SELECTION"
    CHARGING = "CHARGING"
    CHARGING_MEB = "CHARGING_MEB"
    CHARGING_PROFILES = "CHARGING_PROFILES"
    CHARGING_STATIONS = "CHARGING_STATIONS"
    CUBIC = "CUBIC"
    DEALER_APPOINTMENT = "DEALER_APPOINTMENT"
    DESTINATIONS = "DESTINATIONS"
    DESTINATION_IMPORT = "DESTINATION_IMPORT"
    DESTINATION_IMPORT_UPGRADABLE = "DESTINATION_IMPORT_UPGRADABLE"
    DIGICERT = "DIGICERT"
    EMERGENCY_CALLING = "EMERGENCY_CALLING"
    EV_ROUTE_PLANNING = "EV_ROUTE_PLANNING"
    EXTENDED_CHARGING_SETTINGS = "EXTENDED_CHARGING_SETTINGS"
    FUEL_STATUS = "FUEL_STATUS"
    GEO_FENCE = "GEO_FENCE"
    GUEST_USER_MANAGEMENT = "GUEST_USER_MANAGEMENT"
    HONK_AND_FLASH = "HONK_AND_FLASH"
    ICE_VEHICLE_RTS = "ICE_VEHICLE_RTS"
    MAP_UPDATE = "MAP_UPDATE"
    MEASUREMENTS = "MEASUREMENTS"
    MISUSE_PROTECTION = "MISUSE_PROTECTION"
    NEWS = "NEWS"
    ONLINE_SPEECH_GPS = "ONLINE_SPEECH_GPS"
    PARKING_INFORMATION = "PARKING_INFORMATION"
    PARKING_POSITION = "PARKING_POSITION"
    PAY_TO_FUEL = "PAY_TO_FUEL"
    PAY_TO_PARK = "PAY_TO_PARK"
    PLUG_AND_CHARGE = "PLUG_AND_CHARGE"
    POI_SEARCH = "POI_SEARCH"
    POWERPASS_TARIFFS = "POWERPASS_TARIFFS"
    ROADSIDE_ASSISTANT = "ROADSIDE_ASSISTANT"
    ROUTE_IMPORT = "ROUTE_IMPORT"
    ROUTE_PLANNING_5_CHARGERS = "ROUTE_PLANNING_5_CHARGERS"
    ROUTING = "ROUTING"
    SERVICE_PARTNER = "SERVICE_PARTNER"
    SPEED_ALERT = "SPEED_ALERT"
    STATE = "STATE"
    SUBSCRIPTIONS = "SUBSCRIPTIONS"
    TRAFFIC_INFORMATION = "TRAFFIC_INFORMATION"
    TRIP_STATISTICS = "TRIP_STATISTICS"
    VEHICLE_HEALTH_INSPECTION = "VEHICLE_HEALTH_INSPECTION"
    VEHICLE_HEALTH_WARNINGS = "VEHICLE_HEALTH_WARNINGS"
    VEHICLE_HEALTH_WARNINGS_WITH_WAKE_UP = "VEHICLE_HEALTH_WARNINGS_WITH_WAKE_UP"
    VEHICLE_SERVICES_BACKUPS = "VEHICLE_SERVICES_BACKUPS"
    VEHICLE_WAKE_UP = "VEHICLE_WAKE_UP"
    VEHICLE_WAKE_UP_TRIGGER = "VEHICLE_WAKE_UP_TRIGGER"
    WARNING_LIGHTS = "WARNING_LIGHTS"
    WEB_RADIO = "WEB_RADIO"
    WINDOW_HEATING = "WINDOW_HEATING"


class CapabilityStatus(StrEnum):
    DEACTIVATED_BY_ACTIVE_VEHICLE_USER = "DEACTIVATED_BY_ACTIVE_VEHICLE_USER"
    INSUFFICIENT_BATTERY_LEVEL = "INSUFFICIENT_BATTERY_LEVEL"


class Capability(BaseModel):
    id: CapabilityId
    statuses: list[CapabilityStatus]

    def is_available(self) -> bool:
        """Check whether the capability can currently be used."""
        return (
            CapabilityStatus.DEACTIVATED_BY_ACTIVE_VEHICLE_USER not in self.statuses
            and CapabilityStatus.INSUFFICIENT_BATTERY_LEVEL not in self.statuses
        )


class Capabilities(BaseModel):
    capabilities: list[Capability]

    @validator("capabilities", pre=True, always=True)
    def drop_unknown_capabilities(cls, value: list[dict]) -> list[dict]:  # noqa: N805
        """Drop any unknown capabilities and log a message."""
        unknown_capabilities = [c for c in value if c["id"] not in CapabilityId]
        if unknown_capabilities:
            _LOGGER.info(f"Dropping unknown capabilities: {unknown_capabilities}")
        return [c for c in value if c["id"] in CapabilityId]


class Battery(BaseModel):
    capacity: int = Field(None, alias="capacityInKWh")


class BodyType(StrEnum):
    SUV = "SUV"
    COMBI = "Combi"


class VehicleState(StrEnum):
    ACTIVATED = "ACTIVATED"


class Engine(BaseModel):
    power: int = Field(None, alias="powerInKW")
    capacity_in_liters: float | None = Field(None, alias="capacityInLiters")
    type: str


class Gearbox(BaseModel):
    type: str


class Specification(BaseModel):
    battery: Battery | None
    body: BodyType
    engine: Engine
    manufacturing_date: date = Field(None, alias="manufacturingDate")
    max_charging_power: int = Field(None, alias="maxChargingPowerInKW")
    model: str
    model_year: str = Field(None, alias="modelYear")
    system_code: str = Field(None, alias="systemCode")
    system_model_id: str = Field(None, alias="systemModelId")
    title: str
    trim_level: str = Field(None, alias="trimLevel")


class ServicePartner(BaseModel):
    id: str = Field(None, alias="servicePartnerId")


class ErrorType(StrEnum):
    MISSING_RENDER = "MISSING_RENDER"


class Error(BaseModel):
    description: str
    type: ErrorType


class Info(BaseModel):
    """Basic vehicle information."""

    software_version: str = Field(None, alias="softwareVersion")
    state: VehicleState
    specification: Specification
    vin: str
    name: str
    device_platform: str = Field(None, alias="devicePlatform")
    service_partner: ServicePartner = Field(None, alias="servicePartner")
    workshop_mode_enabled: bool = Field(None, alias="workshopModeEnabled")
    capabilities: Capabilities
    errors: list[Error] | None
    license_plate: str = Field(None, alias="licensePlate")

    def has_capability(self, cap: CapabilityId) -> bool:
        """Check for a capability.

        Checks whether a vehicle generally has a capability.
        Does not check whether it's actually available.
        """
        return any(capability.id == cap for capability in self.capabilities.capabilities)

    def is_capability_available(self, cap: CapabilityId) -> bool:
        """Check for capability availability.

        Checks whether the vehicle has the capability and whether it is currently
        available. A capability can be unavailable for example if it's deactivated
        by the currently active user.
        """
        return any(
            capability.id == cap and capability.is_available()
            for capability in self.capabilities.capabilities
        )

    def get_model_name(self) -> str:
        """Return the name of the vehicle's model."""
        model = self.specification.model
        engine = self.specification.engine
        model_year = self.specification.model_year
        system_model_id = self.specification.system_model_id
        return f"{model} {engine} {model_year} ({system_model_id})"
