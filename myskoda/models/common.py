"""Common models used in multiple responses."""

from enum import StrEnum

from pydantic import BaseModel, Field


class OnOffState(StrEnum):
    ON = "ON"
    OFF = "OFF"
    INVALID = "INVALID"


class EnabledState(StrEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class ActiveState(StrEnum):
    ACTIVATED = "ACTIVATED"
    DEACTIVATED = "DEACTIVATED"


class OpenState(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNSUPPORTED = "UNSUPPORTED"


class DoorLockedState(StrEnum):
    LOCKED = "YES"
    UNLOCKED = "NO"
    TRUNK_OPENED = "TRUNK_OPENED"


class ChargerLockedState(StrEnum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"


class ConnectionState(StrEnum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


class Side(StrEnum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class Address(BaseModel):
    city: str
    country: str | None
    country_code: str = Field(None, alias="countryCode")
    house_number: str | None = Field(None, alias="houseNumber")
    street: str
    zip_code: str = Field(None, alias="zipCode")


class Weekday(StrEnum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"
