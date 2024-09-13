from datetime import date
from enum import Enum
from pydantic import BaseModel, Field


class Battery(BaseModel):
    capacity: int = Field(None, alias="capacityInKWh")


class BodyType(str, Enum):
    SUV = "SUV"


class VehicleState(str, Enum):
    ACTIVATED = "ACTIVATED"


class Engine(BaseModel):
    power: int = Field(None, alias="powerInKW")
    type: str


class Gearbox(BaseModel):
    type: str


class Specification(BaseModel):
    battery: Battery
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
