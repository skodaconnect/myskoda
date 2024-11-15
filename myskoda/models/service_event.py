"""Models related to service events from the MQTT broker."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .charging import ChargeMode, ChargingState


class ServiceEventName(StrEnum):
    """List of known Service EventNames."""

    CHANGE_ACCESS = "change-access"
    CHANGE_CHARGE_MODE = "change-charge-mode"
    CHANGE_LIGHTS = "change-lights"
    CHANGE_REMAINING_TIME = "change-remaining-time"
    CHANGE_SOC = "change-soc"
    CHARGING_COMPLETED = "charging-completed"
    CHARGING_STATUS_CHANGED = "charging-status-changed"
    CLIMATISATION_COMPLETED = "climatisation-completed"
    DEPARTURE_STATUS_CHANGED = "departure-status-changed"


@dataclass
class ServiceEventData(DataClassORJSONMixin):
    """Data for Service Events."""

    user_id: str = field(metadata=field_options(alias="userId"))
    vin: str


T = TypeVar("T", bound=ServiceEventData)


@dataclass
class ServiceEvent(Generic[T], DataClassORJSONMixin):
    """Main model for Service Events.

    Service Events are unsolicited events emitted by the MQTT bus towards the client.
    """

    version: int
    producer: str
    name: ServiceEventName
    data: T
    trace_id: str = field(metadata=field_options(alias="traceId"))
    timestamp: datetime | None = field(default=None)


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
        case "chargePurposeReachedAndConservation":
            return ChargingState.CONSERVING
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


def _deserialize_time_to_finish(value: int | str) -> int | None:
    if value == "null":
        return None
    return int(value)


@dataclass
class ServiceEventChargingData(ServiceEventData):
    """Charging Data inside a Service Event."""

    mode: ChargeMode | None = field(
        default=None,
        metadata=field_options(deserialize=_deserialize_mode),
    )
    state: ChargingState | None = field(
        default=None,
        metadata=field_options(deserialize=_deserialize_charging_state),
    )
    soc: int | None = field(default=None)
    charged_range: int | None = field(default=None, metadata=field_options(alias="chargedRange"))
    time_to_finish: int | None = field(
        default=None,
        metadata=field_options(alias="timeToFinish", deserialize=_deserialize_time_to_finish),
    )


@dataclass
class ServiceEventCharging(ServiceEvent, DataClassORJSONMixin):
    """Charging details of a Service Event."""

    data: ServiceEventChargingData


class UnexpectedChargeModeError(Exception):
    pass


class UnexpectedChargingStateError(Exception):
    pass
