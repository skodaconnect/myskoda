"""Models for responses of api/v2/air-conditioning endpoint."""

import json
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
    COOLING = "COOLING"
    HEATING = "HEATING"
    HEATING_AUXILIARY = "HEATING_AUXILIARY"
    OFF = "OFF"
    ON = "ON"
    VENTILATION = "VENTILATION"
    INVALID = "INVALID"


# Probaly other states than AUTOMATIC are available, to be discovered
class HeaterSource(StrEnum):
    AUTOMATIC = "AUTOMATIC"
    ELECTRIC = "ELECTRIC"


@dataclass
class AuxiliaryConfig(DataClassORJSONMixin):
    target_temperature: float | None = None
    duration: int | None = None
    source: HeaterSource | None = None
    mode: AirConditioningState | None = None

    @property
    def to_json(self) -> dict[str, Any]:
        """Build a JSON-compatible dictionary based on the AuxiliaryConfig attributes.

        Returns:
            Dict[str, Any]: A dictionary containing the serialized configuration.
            Keys are included only if their corresponding attributes are not None.

        """
        json_data = {}

        if self.target_temperature is not None:
            round_temp = f"{round(self.target_temperature * 2) / 2:.1f}"
            json_data["targetTemperature"] = {
                "temperatureValue": round_temp,
                "unitInCar": "CELSIUS",
            }

        if self.duration is not None:
            json_data["durationInSeconds"] = str(self.duration)

        if self.source is not None:
            json_data["heaterSource"] = self.source.value

        if self.mode is not None:
            json_data["startMode"] = self.mode.value

        return json_data


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
    errors: list[Any]
    state: AirConditioningState
    steering_wheel_position: Side = field(metadata=field_options(alias="steeringWheelPosition"))
    window_heating_state: WindowHeatingState = field(
        metadata=field_options(alias="windowHeatingState")
    )
    car_captured_timestamp: datetime | None = field(
        default=None, metadata=field_options(alias="carCapturedTimestamp")
    )
    air_conditioning_at_unlock: bool | None = field(
        default=None, metadata=field_options(alias="airConditioningAtUnlock")
    )
    charger_connection_state: ConnectionState | None = field(
        default=None, metadata=field_options(alias="chargerConnectionState")
    )
    charger_lock_state: ChargerLockedState | None = field(
        default=None, metadata=field_options(alias="chargerLockState")
    )
    estimated_date_time_to_reach_target_temperature: datetime | None = field(
        default=None, metadata=field_options(alias="estimatedDateTimeToReachTargetTemperature")
    )
    heater_source: HeaterSource | None = field(
        default=None, metadata=field_options(alias="heaterSource")
    )
    seat_heating_activated: SeatHeating | None = field(
        default=None, metadata=field_options(alias="seatHeatingActivated")
    )
    target_temperature: TargetTemperature | None = field(
        default=None, metadata=field_options(alias="targetTemperature")
    )
    window_heating_enabled: bool | None = field(
        default=None, metadata=field_options(alias="windowHeatingEnabled")
    )
    air_conditioning_without_external_power: bool | None = field(
        default=None, metadata=field_options(alias="airConditioningWithoutExternalPower")
    )
