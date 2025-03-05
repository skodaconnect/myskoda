"""Models for responses of api/v2/vehicle-status/{vin}/driving-range."""

from dataclasses import dataclass, field
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import Address, BaseResponse, Coordinates


class PositionType(StrEnum):
    VEHICLE = "VEHICLE"


@dataclass
class Position(DataClassORJSONMixin):
    address: Address
    gps_coordinates: Coordinates = field(metadata=field_options(alias="gpsCoordinates"))
    type: PositionType


class ErrorType(StrEnum):
    VEHICLE_IN_MOTION = "VEHICLE_IN_MOTION"
    VEHICLE_POSITION_UNAVAILABLE = "VEHICLE_POSITION_UNAVAILABLE"


@dataclass
class Error(DataClassORJSONMixin):
    type: ErrorType
    description: str


@dataclass
class Positions(BaseResponse):
    """Positional information (GPS) for the vehicle and other things."""

    errors: list[Error]
    positions: list[Position]
