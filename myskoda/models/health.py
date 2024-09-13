from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any


class WarningLightCategory(str, Enum):
    ASSISTANCE = "ASSISTANCE"
    COMFORT = "COMFORT"
    BRAKE = "BRAKE"
    ELECTRIC_ENGINE = "ELECTRIC_ENGINE"
    LIGHTING = "LIGHTING"
    TIRE = "TIRE"
    OTHER = "OTHER"


class WarningLight(BaseModel):
    category: WarningLightCategory
    defects: list[Any]


class Health(BaseModel):
    """Information about the car's health (currently only mileage)."""

    captured_at: datetime = Field(None, alias="capturedAt")
    mileage_in_km: int = Field(None, alias="mileageInKm")
    warning_lights: list[WarningLight] = Field(None, alias="warningLights")
