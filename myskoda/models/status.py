"""Models for responses of api/v2/vehicle-status/{vin}."""

from dataclasses import dataclass, field
from datetime import datetime

from mashumaro import field_options
from mashumaro.mixins.json import DataClassJSONMixin

from myskoda.models.common import DoorLockedState, OnOffState, OpenState


@dataclass
class Detail(DataClassJSONMixin):
    bonnet: OpenState
    sunroof: OpenState
    trunk: OpenState


@dataclass
class Overall(DataClassJSONMixin):
    doors: OpenState
    doors_locked: DoorLockedState = field(metadata=field_options(alias="doorsLocked"))
    lights: OnOffState
    locked: DoorLockedState
    windows: OpenState


@dataclass
class Status(DataClassJSONMixin):
    """Current status information for a vehicle."""

    car_captured_timestamp: datetime = field(metadata=field_options(alias="carCapturedTimestamp"))
    detail: Detail
    overall: Overall
