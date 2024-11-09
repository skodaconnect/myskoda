"""Models for responses of api/v2/vehicle-status/{vin}."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


class VehicleType(StrEnum):
    FUEL = "FUEL"
    HYBRID = "HYBRID"
    ELECTRIC = "ELECTRIC"


@dataclass
class StatisticsEntry(DataClassORJSONMixin):
    date: date
    average_fuel_consumption: float | None = field(
        default=None, metadata=field_options(alias="averageFuelConsumption")
    )
    average_speed_in_kmph: int | None = field(
        default=None, metadata=field_options(alias="averageSpeedInKmph")
    )
    average_electric_consumption: float | None = field(
        default=None, metadata=field_options(alias="averageElectricConsumption")
    )
    average_recuperation: float | None = field(
        default=None, metadata=field_options(alias="averageRecuperation")
    )
    average_aux_consumption: float | None = field(
        default=None, metadata=field_options(alias="averageAuxConsumption")
    )
    mileage_in_km: int | None = field(default=None, metadata=field_options(alias="mileageInKm"))
    travel_time_in_min: int | None = field(
        default=None, metadata=field_options(alias="travelTimeInMin")
    )
    trip_ids: list[int] | None = field(default=None, metadata=field_options(alias="tripIds"))


@dataclass
class TripStatistics(DataClassORJSONMixin):
    vehicle_type: VehicleType = field(metadata=field_options(alias="vehicleType"))
    detailed_statistics: list[StatisticsEntry] = field(
        metadata=field_options(alias="detailedStatistics")
    )
    overall_average_electric_consumption: float | None = field(
        default=None, metadata=field_options(alias="overallAverageElectricConsumption")
    )
    overall_average_fuel_consumption: float | None = field(
        default=None, metadata=field_options(alias="overallAverageFuelConsumption")
    )
    overall_average_mileage_in_km: int | None = field(
        default=None, metadata=field_options(alias="overallAverageMileageInKm")
    )
    overall_average_speed_in_kmph: int | None = field(
        default=None, metadata=field_options(alias="overallAverageSpeedInKmph")
    )
    overall_average_travel_time_in_min: int | None = field(
        default=None, metadata=field_options(alias="overallAverageTravelTimeInMin")
    )
    overall_mileage_in_km: int | None = field(
        default=None, metadata=field_options(alias="overallMileageInKm")
    )
    overall_travel_time_in_min: int | None = field(
        default=None, metadata=field_options(alias="overallTravelTimeInMin")
    )
