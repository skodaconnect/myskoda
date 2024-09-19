"""Models related to service events from the MQTT broker."""

from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class ServiceEventName(StrEnum):
    CHANGE_SOC = "change-soc"
    CHANGE_ACCESS = "change-access"
    CHANGE_LIGHTS = "change-lights"
    CLIMATISATION_COMPLETED = "climatisation-completed"
    CHANGE_REMAINING_TIME = "change-remaining-time"
    CHANGE_CHARGE_MODE = "change-charge-mode"


class ServiceEventData(BaseModel):
    user_id: str = Field(None, alias="userId")
    vin: str


T = TypeVar("T", bound=ServiceEventData)


class ServiceEvent(BaseModel, Generic[T]):
    version: int
    trace_id: str = Field(None, alias="traceId")
    timestamp: datetime = Field(None, alias="requestId")
    producer: str
    name: ServiceEventName
    data: T


class ServiceEventChargingState(StrEnum):
    CHARGING = "charging"
    CHARGED_NOT_CONSERVING = "chargePurposeReachedAndNotConservationCharging"
    NOT_READY = "notReadyForCharging"
    READY = "readyForCharging"


class ServiceEventChargeMode(StrEnum):
    HOME_STORAGE_CHARGING = "homeStorageCharging"
    IMMEDIATE_DISCHARGING = "immediateDischarging"
    ONLY_OWN_CURRENT = "onlyOwnCurrent"
    PREFERRED_CHARGING_TIMES = "preferredChargingTimes"
    TIMER_CHARGING_WITH_CLIMATISATION = "timerChargingWithClimatisation"
    TIMER = "timer"
    MANUAL = "manual"
    OFF = "off"


class ServiceEventChargingData(ServiceEventData):
    mode: ServiceEventChargeMode
    state: ServiceEventChargingState
    soc: int
    charged_range: int = Field(None, alias="chargedRange")
    time_to_finish: int | None = Field(None, alias="timeToFinish")


class ServiceEventCharging(ServiceEvent):
    data: ServiceEventChargingData
