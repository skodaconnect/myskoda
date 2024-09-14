"""Models for responses of api/v2/vehicle-status/{vin}."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class VehicleType(StrEnum):
    FUEL = "FUEL"


class StatisticsEntry(BaseModel):
    date: date
    average_fuel_consumption: float | None = Field(None, alias="averageFuelConsumption")
    average_speed_in_kmph: int | None = Field(None, alias="averageSpeedInKmph")
    mileage_in_km: int | None = Field(None, alias="mileageInKm")
    travel_time_in_min: int | None = Field(None, alias="travelTimeInMin")
    trip_ids: list[int] | None = Field(None, alias="tripIds")


class TripStatistics(BaseModel):
    overall_average_fuel_consumption: float = Field(None, alias="overallAverageFuelConsumption")
    overall_average_mileage_in_km: int = Field(None, alias="overallAverageMileageInKm")
    overall_average_speed_in_kmph: int = Field(None, alias="overallAverageSpeedInKmph")
    overall_average_travel_time_in_min: int = Field(None, alias="overallAverageTravelTimeInMin")
    overall_mileage_in_km: int = Field(None, alias="overallMileageInKm")
    overall_travel_time_in_min: int = Field(None, alias="overallTravelTimeInMin")
    vehicle_type: VehicleType = Field(None, alias="vehicleType")
    detailed_statistics: list[StatisticsEntry] = Field(None, alias="detailedStatistics")
