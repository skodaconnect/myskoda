"""Models for responses of api/v2/air-conditioning endpoint."""

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import StrEnum
from typing import Any

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import ChargerLockedState, ConnectionState, OnOffState, Side, Weekday


class TemperatureUnit(StrEnum):
    CELSIUS = "CELSIUS"


class TimerMode(StrEnum):
    ONE_OFF = "ONE_OFF"
    RECURRING = "RECURRING"


class AirConditioningState(StrEnum):
    ON = "ON"
    OFF = "OFF"
    HEATING = "HEATING"
    VENTILATION = "VENTILATION"


@dataclass
class Timer(DataClassORJSONMixin):
    enabled: bool
    id: int
    time: time
    type: TimerMode
    selected_days: list[Weekday] = field(metadata=field_options(alias="selectedDays"))


@dataclass
class SeatHeating(DataClassORJSONMixin):
    front_left: bool = field(metadata=field_options(alias="frontLeft"))
    front_right: bool = field(metadata=field_options(alias="frontRight"))


@dataclass
class TargetTemperature(DataClassORJSONMixin):
    temperature_value: float = field(metadata=field_options(alias="temperatureValue"))
    unit_in_car: TemperatureUnit = field(metadata=field_options(alias="unitInCar"))


@dataclass
class WindowHeatingState(DataClassORJSONMixin):
    front: OnOffState
    rear: OnOffState
    unspecified: Any


@dataclass
class AirConditioning(DataClassORJSONMixin):
    """Information related to air conditioning."""

    timers: list[Timer]
    air_conditioning_at_unlock: bool = field(
        metadata=field_options(alias="airConditioningAtUnlock")
    )
    car_captured_timestamp: datetime = field(metadata=field_options(alias="carCapturedTimestamp"))
    charger_connection_state: ConnectionState = field(
        metadata=field_options(alias="chargerConnectionState")
    )
    charger_lock_state: ChargerLockedState = field(metadata=field_options(alias="chargerLockState"))
    errors: list[Any]
    estimated_date_time_to_reach_target_temperature: datetime = field(
        metadata=field_options(alias="estimatedDateTimeToReachTargetTemperature")
    )
    state: AirConditioningState
    steering_wheel_position: Side = field(metadata=field_options(alias="steeringWheelPosition"))
    window_heating_enabled: bool = field(metadata=field_options(alias="windowHeatingEnabled"))
    window_heating_state: WindowHeatingState = field(
        metadata=field_options(alias="windowHeatingState")
    )
    seat_heating_activated: SeatHeating | None = field(
        default=None, metadata=field_options(alias="seatHeatingActivated")
    )
    target_temperature: TargetTemperature | None = field(
        default=None, metadata=field_options(alias="targetTemperature")
    )
