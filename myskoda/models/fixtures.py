"""Models for fixtures."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.mixins.yaml import DataClassYAMLMixin

from myskoda.models.info import Capability, Info


class Endpoint(StrEnum):
    LIST_VEHICLES = "LIST_VEHICLES"
    INFO = "INFO"
    STATUS = "STATUS"
    AIR_CONDITIONING = "AIR_CONDITIONING"
    POSITIONS = "POSITIONS"
    HEALTH = "HEALTH"
    CHARGING = "CHARGING"
    MAINTENANCE = "MAINTENANCE"
    DRIVING_RANGE = "DRIVING_RANGE"
    USER = "USER"
    TRIP_STATISTICS = "TRIP_STATISTICS"
    GARAGE = "GARAGE"
    ALL = "ALL"


@dataclass
class FixtureGet(DataClassYAMLMixin):
    vehicle_id: int
    raw: str
    success: bool
    error: str
    url: str
    result: dict
    endpoint: Endpoint


@dataclass
class FixtureVehicle(DataClassYAMLMixin):
    id: int
    device_platform: str
    system_model_id: str
    model: str
    model_year: str
    trim_level: str | None
    software_version: str | None
    capabilities: list[Capability]


def create_fixture_vehicle(id: int, info: Info) -> FixtureVehicle:  # noqa: A002
    """Create a new `FixtureVehicle` from an info."""
    return FixtureVehicle(
        id=id,
        device_platform=info.device_platform,
        system_model_id=info.specification.system_model_id,
        capabilities=info.capabilities.capabilities,
        model=info.specification.model,
        model_year=info.specification.model_year,
        software_version=info.software_version,
        trim_level=info.specification.trim_level,
    )


@dataclass
class Fixture(DataClassORJSONMixin, DataClassYAMLMixin):
    """A fixture for a test generated by the CLI."""

    name: str
    description: str | None
    generation_time: datetime
    vehicles: list[FixtureVehicle]
    get: list[FixtureGet] | None
