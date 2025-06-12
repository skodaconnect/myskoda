"""Common models used in multiple responses."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Optional

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

type Vin = str


class CaseInsensitiveStrEnum(StrEnum):
    @classmethod
    def _missing_(cls, value: object) -> StrEnum | None:
        """Ignore the case of the value.

        Some endpoints will return values sometimes as uppercase and sometimes as lowercase...
        """
        if not isinstance(value, str):
            raise TypeError
        value = value.lower()
        for member in cls:
            if member.lower() == value:
                return member
        return None


class OnOffState(StrEnum):
    ON = "ON"
    OFF = "OFF"
    INVALID = "INVALID"


class EnabledState(StrEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    NOT_ALLOWED = "NOT_ALLOWED"


class ActiveState(StrEnum):
    ACTIVATED = "ACTIVATED"
    DEACTIVATED = "DEACTIVATED"


class OpenState(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


class DoorLockedState(StrEnum):
    LOCKED = "YES"
    OPENED = "OPENED"
    TRUNK_OPENED = "TRUNK_OPENED"
    UNLOCKED = "NO"
    UNKNOWN = "UNKNOWN"


class ChargerLockedState(StrEnum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    INVALID = "INVALID"


class ConnectionState(StrEnum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


class Side(StrEnum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


@dataclass
class Coordinates(DataClassORJSONMixin):
    """GPS Coordinates."""

    latitude: float
    longitude: float


@dataclass
class Address(DataClassORJSONMixin):
    """A representation of a house-address."""

    country_code: str = field(metadata=field_options(alias="countryCode"))
    zip_code: str | None = field(default=None, metadata=field_options(alias="zipCode"))
    house_number: str | None = field(default=None, metadata=field_options(alias="houseNumber"))
    street: str | None = field(default=None)
    city: str | None = field(default=None)
    country: str | None = field(default=None)


class Weekday(StrEnum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


@dataclass
class BaseResponse(DataClassORJSONMixin):
    """Base class for all API response models.

    All responses have the current timestamp injected.
    """

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC), kw_only=True)


class PercentageValueError(ValueError):
    """Custom error message for Percentage invalid values."""

    def __init__(self, value: int) -> None:
        self.value = value
        super().__init__(f"Percentage must be between 0 and 100, got {self.value}")


@dataclass(frozen=True)
class Percentage(DataClassORJSONMixin):
    value: int

    def __post_init__(self) -> None:
        """Validate that the percentage value is within 0 to 100 inclusive.

        Raises:
            PercentageValueError: If `value` is outside the valid percentage range.

        """
        if not (0 <= self.value <= 100):  # noqa: PLR2004
            raise PercentageValueError(self.value)

    @classmethod
    def _deserialize(
        cls, value: object, _type: type, _context: Mapping[str, object]
    ) -> Optional["Percentage"]:
        if value is None:
            return None
        if not isinstance(value, int):
            return None
        if not (0 <= value <= 100):  # noqa: PLR2004
            return None
        return cls(value)
