"""Models for responses of api/v2/vehicle-status/{vin}/driving-range endpoint."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


class EngineType(StrEnum):
    DIESEL = "diesel"
    ELECTRIC = "electric"


@dataclass
class EngineRange(DataClassORJSONMixin):
    current_soc_in_percent: int = field(metadata=field_options(alias="currentSoCInPercent"))
    engine_type: EngineType = field(metadata=field_options(alias="engineType"))
    remaining_range_in_km: int = field(metadata=field_options(alias="remainingRangeInKm"))
    current_fuel_level_in_percent: int | None = field(
        default=None, metadata=field_options(alias="currentFuelLevelInPercent")
    )


@dataclass
class DrivingRange(DataClassORJSONMixin):
    car_captured_timestamp: datetime = field(metadata=field_options(alias="carCapturedTimestamp"))
    car_type: EngineType = field(metadata=field_options(alias="carType"))
    primary_engine_range: EngineRange = field(metadata=field_options(alias="primaryEngineRange"))
    total_range_in_km: int = field(metadata=field_options(alias="totalRangeInKm"))
