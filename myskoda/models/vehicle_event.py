"""Models related to vehicle events from the MQTT broker."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from myskoda.models.vehicle_ignition_status import IgnitionStatus, UnexpectedIgnitionStatusError


class VehicleEventName(StrEnum):
    """List of known vehicle EventNames."""

    VEHICLE_AWAKE = "vehicle-awake"
    VEHICLE_CONNECTION_ONLINE = "vehicle-connection-online"
    VEHICLE_WARNING_BATTEYLEVEL = "vehicle-warning-batterylevel"
    VEHICLE_IGNITION_STATUS_CHANGED = "vehicle-ignition-status-changed"


@dataclass
class VehicleEventData(DataClassORJSONMixin):
    """Base class for data in vehicle events."""

    user_id: str = field(metadata=field_options(alias="userId"))
    vin: str


T = TypeVar("T", bound=VehicleEventData)


@dataclass
class VehicleEvent(Generic[T], DataClassORJSONMixin):
    """Main model for Vehicle Events.

    Vehicle Events are unsolicited events emitted by the MQTT bus towards the client.
    """

    version: int
    producer: str
    name: VehicleEventName
    data: T
    trace_id: str = field(metadata=field_options(alias="traceId"))
    timestamp: datetime | None = field(default=None)


def _deserialize_ignition_status(value: str) -> IgnitionStatus:
    match value:
        case "ON":
            return IgnitionStatus.ON
        case "OFF":
            return IgnitionStatus.OFF
        case _:
            raise UnexpectedIgnitionStatusError


@dataclass
class VehicleEventVehicleIgnitionStatusData(VehicleEventData):
    """Ignition data inside vehicle service event vehicle-ignition-status."""

    ignition_status: IgnitionStatus | None = field(
        default=None,
        metadata=field_options(alias="ignitionStatus", deserialize=_deserialize_ignition_status),
    )


@dataclass
class VehicleEventWithVehicleIgnitionStatusData(VehicleEvent):
    data: VehicleEventVehicleIgnitionStatusData
