from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Any

from .common import Address, Coordinates


class Type(StrEnum):
    VEHICLE = "VEHICLE"


class Position(BaseModel):
    address: Address
    gps_coordinates: Coordinates = Field(None, alias="gpsCoordinates")
    type: Type


class Positions(BaseModel):
    """Positional information (GPS) for the vehicle and other things."""

    errors: list[Any]
    positions: list[Position]
