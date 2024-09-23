"""Common models used in multiple responses."""

from dataclasses import dataclass, field
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.json import DataClassJSONMixin


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
    OPENED = "OPENED"
    TRUNK_OPENED = "TRUNK_OPENED"
    UNLOCKED = "NO"


class ChargerLockedState(StrEnum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"


class ConnectionState(StrEnum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


class Side(StrEnum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


@dataclass
class Coordinates(DataClassJSONMixin):
    latitude: float
    longitude: float


@dataclass
class Address(DataClassJSONMixin):
    city: str
    street: str
    country_code: str = field(metadata=field_options(alias="countryCode"))
    zip_code: str = field(metadata=field_options(alias="zipCode"))
    house_number: str | None = field(default=None, metadata=field_options(alias="houseNumber"))
    country: str | None = field(default=None)


class Weekday(StrEnum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"
