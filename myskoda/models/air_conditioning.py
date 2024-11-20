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
    COOLING = "COOLING"
    HEATING = "HEATING"
    HEATING_AUXILIARY = "HEATING_AUXILIARY"
    OFF = "OFF"
    ON = "ON"
    VENTILATION = "VENTILATION"
    INVALID = "INVALID"


# Probably other states than AUTOMATIC are available, to be discovered
class HeaterSource(StrEnum):
    AUTOMATIC = "AUTOMATIC"
    ELECTRIC = "ELECTRIC"


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
    unit_in_car: TemperatureUnit = field(
        default=TemperatureUnit.CELSIUS, metadata=field_options(alias="unitInCar")
    )


@dataclass
class WindowHeatingState(DataClassORJSONMixin):
    front: OnOffState
    rear: OnOffState
    unspecified: Any


@dataclass
class AuxiliaryConfig(DataClassORJSONMixin):
    target_temperature: TargetTemperature | None = field(
        default=None, metadata=field_options(alias="targetTemperature")
    )
    duration_in_seconds: int | None = field(
        default=None, metadata=field_options(alias="durationInSeconds")
    )
    heater_source: HeaterSource | None = field(
        default=None, metadata=field_options(alias="heaterSource")
    )
    start_mode: AirConditioningState | None = field(
        default=None, metadata=field_options(alias="startMode")
    )

    def get_config(self) -> dict[str, object]:
        """Get the dict from AuxiliaryConfig without None values and with aliases."""
        result = {}
        # Handle fields with aliases and None values
        for field_name, field_value in self.__dict__.items():
            field_info = self.__dataclass_fields__.get(field_name)

            # Ensure field_info exists before accessing its metadata
            if field_info is None:
                continue

            alias = field_info.metadata.get("alias", field_name)  # Use alias if available

            if field_value is not None:  # Only include non-None values
                # Special handling for target_temperature
                if field_name == "target_temperature" and isinstance(
                    field_value, TargetTemperature
                ):
                    round_temp = round(field_value.temperature_value * 2) / 2
                    result[alias] = {
                        "temperatureValue": float(round_temp),
                        "unitInCar": field_value.unit_in_car,
                    }
                else:
                    result[alias] = field_value

        return result


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
