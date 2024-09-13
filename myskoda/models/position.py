from enum import Enum
from pydantic import BaseModel, Field
from typing import Any

from .common import Address, Coordinates


class Type(str, Enum):
    VEHICLE = "VEHICLE"


class Position(BaseModel):
    address: Address
    gps_coordinates: Coordinates = Field(None, alias="gpsCoordinates")
    type: Type


class Positions(BaseModel):
    """Positional information (GPS) for the vehicle and other things."""

    errors: list[Any]
    positions: list[Position]
