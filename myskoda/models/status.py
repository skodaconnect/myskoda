"""Models for responses of api/v2/vehicle-status/{vin}."""

from dataclasses import dataclass, field
from datetime import datetime

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from myskoda.models.common import DoorLockedState, OnOffState, OpenState


@dataclass
class Detail(DataClassORJSONMixin):
    bonnet: OpenState
    sunroof: OpenState
    trunk: OpenState


@dataclass
class Overall(DataClassORJSONMixin):
    doors: OpenState
    doors_locked: DoorLockedState = field(metadata=field_options(alias="doorsLocked"))
    lights: OnOffState
    locked: DoorLockedState
    windows: OpenState


@dataclass
class Status(DataClassORJSONMixin):
    """Current status information for a vehicle."""

    detail: Detail
    overall: Overall
    car_captured_timestamp: datetime | None = field(
        default=None, metadata=field_options(alias="carCapturedTimestamp")
    )
