"""Models for responses of api/v2/vehicle-status/{vin}/driving-range endpoint."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EngineType(StrEnum):
    DIESEL = "diesel"
    ELECTRIC = "electric"


class EngineRange(BaseModel):
    current_fuel_level_in_percent: int = Field(None, alias="currentFuelLevelInPercent")
    current_so_c_in_percent: int = Field(None, alias="currentSoCInPercent")
    engine_type: EngineType = Field(None, alias="engineType")
    remaining_range_in_km: int = Field(None, alias="remainingRangeInKm")


class DrivingRange(BaseModel):
    car_captured_timestamp: datetime = Field(None, alias="carCapturedTimestamp")
    car_type: EngineType = Field(None, alias="carType")
    primary_engine_range: EngineRange = Field(None, alias="primaryEngineRange")
    total_range_in_km: int = Field(None, alias="totalRangeInKm")
