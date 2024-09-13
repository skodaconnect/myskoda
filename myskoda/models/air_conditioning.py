from datetime import datetime, time
from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Any

from .common import ChargerLockedState, ConnectionState, OnOffState, Side, Weekday


class TemperatureUnit(StrEnum):
    CELSIUS = "CELSIUS"


class TimerMode(StrEnum):
    ONE_OFF = "ONE_OFF"
    RECURRING = "RECURRING"


class Timer(BaseModel):
    enabled: bool
    id: int
    selected_days: list[Weekday] = Field(None, alias="selectedDays")
    time: time
    type: TimerMode


class SeatHeating(BaseModel):
    front_left: bool = Field(None, alias="frontLeft")
    front_right: bool = Field(None, alias="frontRight")


class TargetTemperature(BaseModel):
    temperature_value: float = Field(None, alias="temperatureValue")
    unit_in_car: TemperatureUnit = Field(None, alias="unitInCar")


class WindowHeatingState(BaseModel):
    front: OnOffState
    rear: OnOffState
    unspecified: Any


class AirConditioning(BaseModel):
    """Information related to air conditioning."""

    air_conditioning_at_unlock: bool = Field(None, alias="airConditioningAtUnlock")
    car_captured_timestamp: datetime = Field(None, alias="carCapturedTimestamp")
    charger_connection_state: ConnectionState = Field(
        None, alias="chargerConnectionState"
    )
    charger_lock_state: ChargerLockedState = Field(None, alias="chargerLockState")
    errors: list[Any]
    estimated_date_time_to_reach_target_temperature: datetime = Field(
        None, alias="estimatedDateTimeToReachTargetTemperature"
    )
    seat_heating_activated: SeatHeating = Field(None, alias="seatHeatingActivated")
    state: OnOffState
    steering_wheel_position: Side = Field(None, alias="steeringWheelPosition")
    target_temperature: TargetTemperature | None = Field(
        None, alias="targetTemperature"
    )
    timers: list[Timer]
    window_heating_enabled: bool = Field(None, alias="windowHeatingEnabled")
    window_heating_state: WindowHeatingState = Field(None, alias="windowHeatingState")
