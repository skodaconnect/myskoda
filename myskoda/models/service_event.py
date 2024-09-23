"""Models related to service events from the MQTT broker."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from mashumaro import field_options
from mashumaro.mixins.json import DataClassJSONMixin

from .charging import ChargeMode, ChargingState


class ServiceEventName(StrEnum):
    CHANGE_SOC = "change-soc"
    CHANGE_ACCESS = "change-access"
    CHANGE_LIGHTS = "change-lights"
    CLIMATISATION_COMPLETED = "climatisation-completed"
    CHANGE_REMAINING_TIME = "change-remaining-time"
    CHANGE_CHARGE_MODE = "change-charge-mode"


@dataclass
class ServiceEventData(DataClassJSONMixin):
    user_id: str = field(metadata=field_options(alias="userId"))
    vin: str


T = TypeVar("T", bound=ServiceEventData)


@dataclass
class ServiceEvent(Generic[T], DataClassJSONMixin):
    version: int
    producer: str
    name: ServiceEventName
    data: T
    trace_id: str = field(metadata=field_options(alias="traceId"))
    timestamp: datetime | None = field(default=None, metadata=field_options(alias="requestId"))


def _deserialize_mode(value: str) -> ChargeMode:  # noqa: PLR0911
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


def _deserialize_charging_state(value: str) -> ChargingState:
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


@dataclass
class ServiceEventChargingData(ServiceEventData):
    mode: ChargeMode
    state: ChargingState
    soc: int
    charged_range: int = field(
        metadata=field_options(alias="chargedRange", deserialize=_deserialize_charging_state)
    )
    time_to_finish: int | None = field(
        default=None,
        metadata=field_options(alias="timeToFinish", deserialize=_deserialize_mode),
    )


@dataclass
class ServiceEventCharging(ServiceEvent):
    data: ServiceEventChargingData


class UnexpectedChargeModeError(Exception):
    pass


class UnexpectedChargingStateError(Exception):
    pass
