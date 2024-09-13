from enum import Enum
from pydantic import BaseModel, Field


class OnOffState(str, Enum):
    ON = "ON"
    OFF = "OFF"


class EnabledState(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class ActiveState(str, Enum):
    ACTIVATED = "ACTIVATED"
    DEACTIVATED = "DEACTIVATED"


class OpenState(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNSUPPORTED = "UNSUPPORTED"


class DoorLockedState(str, Enum):
    LOCKED = "YES"
    UNLOCKED = "NO"


class ChargerLockedState(str, Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"


class ConnectionState(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


class Side(str, Enum):
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


class Weekday(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"
