from datetime import datetime
from pydantic import BaseModel, Field

from myskoda.models.common import DoorLockedState, OnOffState, OpenState


class Detail(BaseModel):
    bonnet: OpenState
    sunroof: OpenState
    trunk: OpenState


class Overall(BaseModel):
    doors: OpenState
    doors_locked: DoorLockedState = Field(None, alias="doorsLocked")
    lights: OnOffState
    locked: DoorLockedState
    windows: OpenState


class Status(BaseModel):
    """Current status information for a vehicle."""

    car_captured_timestamp: datetime = Field(None, alias="carCapturedTimestamp")
    detail: Detail
    overall: Overall
