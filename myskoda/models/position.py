from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Any

from .common import Address, Coordinates


class PositionType(StrEnum):
    VEHICLE = "VEHICLE"


class Position(BaseModel):
    address: Address
    gps_coordinates: Coordinates = Field(None, alias="gpsCoordinates")
    type: PositionType


class ErrorType(StrEnum):
    VEHICLE_IN_MOTION = "VEHICLE_IN_MOTION"


class Error(BaseModel):
    type: ErrorType
    description: str


class Positions(BaseModel):
    """Positional information (GPS) for the vehicle and other things."""

    errors: list[Error]
    positions: list[Position]
