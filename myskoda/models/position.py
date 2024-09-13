from enum import Enum
from pydantic import BaseModel, Field
from typing import Any


class Type(str, Enum):
    VEHICLE = "VEHICLE"


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class Address(BaseModel):
    city: str
    country: str
    country_code: str = Field(None, alias="countryCode")
    house_number: str = Field(None, alias="houseNumber")
    street: str
    zip_code: str = Field(None, alias="zipCode")


class Position(BaseModel):
    address: Address
    gps_coordinates: Coordinates = Field(None, alias="gpsCoordinates")
    type: Type


class Positions(BaseModel):
    """Positional information (GPS) for the vehicle and other things."""

    errors: list[Any]
    positions: list[Position]
