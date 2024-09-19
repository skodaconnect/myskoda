"""Models related to service events from the MQTT broker."""

from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, validator

from .charging import ChargeMode, ChargingState


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


class ServiceEventChargingData(ServiceEventData):
    mode: ChargeMode
    state: ChargingState
    soc: int
    charged_range: int = Field(None, alias="chargedRange")
    time_to_finish: int | None = Field(None, alias="timeToFinish")

    @validator("mode", pre=True, always=True)
    def _validator_mode(cls, value: str) -> ChargeMode:  # noqa: N805, PLR0911
        match value:
            case "homeStorageCharging":
                return ChargeMode.HOME_STORAGE_CHARGING
            case "immediateDischarging":
                return ChargeMode.IMMEDIATE_DISCHARGING
            case "onlyOwnCurrent":
                return ChargeMode.ONLY_OWN_CURRENT
            case "preferredChargingTimes":
                return ChargeMode.PREFERRED_CHARGING_TIMES
            case "timerChargingWithClimatisation":
                return ChargeMode.TIMER_CHARGING_WITH_CLIMATISATION
            case "timer":
                return ChargeMode.TIMER
            case "manual":
                return ChargeMode.MANUAL
            case "off":
                return ChargeMode.OFF
            case _:
                raise UnexpectedChargeModeError

    @validator("state", pre=True, always=True)
    def _validator_charging_state(cls, value: str) -> ChargingState:  # noqa: N805
        match value:
            case "charging":
                return ChargingState.CHARGING
            case "chargePurposeReachedAndNotConservationCharging":
                return ChargingState.READY_FOR_CHARGING
            case "notReadyForCharging":
                return ChargingState.CONNECT_CABLE
            case "readyForCharging":
                return ChargingState.READY_FOR_CHARGING
            case "conserving":
                return ChargingState.CONSERVING
            case _:
                raise UnexpectedChargingStateError


class ServiceEventCharging(ServiceEvent):
    data: ServiceEventChargingData


class UnexpectedChargeModeError(Exception):
    pass


class UnexpectedChargingStateError(Exception):
    pass
