"""Models for responses of api/v1/charging/vin/profiles endpoint."""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any

from mashumaro import field_options
from mashumaro.config import (
    TO_DICT_ADD_BY_ALIAS_FLAG,
    BaseConfig,
)
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .air_conditioning import TimerMode
from .charging import MaxChargeCurrent, PlugUnlockMode
from .common import BaseResponse, Coordinates, Weekday


@dataclass
class ChargingTimes(DataClassORJSONMixin):
    """Times a charging profile can be active."""

    id: int
    enabled: bool
    start_time: time = field(metadata=field_options(alias="startTime"))
    end_time: time = field(metadata=field_options(alias="endTime"))

    class Config(BaseConfig):
        """Configuration for serialization and deserialization.."""

        code_generation_options = [  # noqa: RUF012
            TO_DICT_ADD_BY_ALIAS_FLAG
        ]

    def __post_serialize__(self, d: dict[Any, Any]) -> dict[Any, Any]:
        """Post-process the data before serialization."""
        # only execute if serialization was called with byAlias = true
        # to ensure the key is not added otherwise
        if self.start_time and "startTime" in d:
            d["startTime"] = self.start_time.strftime("%H:%M")  # Format to hh:mm

        # only execute if serialization was called with byAlias = true
        # to ensure the key is not added otherwise
        if self.end_time and "endTime" in d:
            d["endTime"] = self.end_time.strftime("%H:%M")  # Format to hh:mm
        return d


@dataclass
class MinBatterySOC(DataClassORJSONMixin):
    """Settings for minimal battery SOC."""

    class Config(BaseConfig):
        """Configuration for serialization and deserialization.."""

        code_generation_options = [  # noqa: RUF012
            TO_DICT_ADD_BY_ALIAS_FLAG
        ]

    minimum_battery_state_of_charge_in_percent: int = field(
        metadata=field_options(alias="minimumBatteryStateOfChargeInPercent")
    )


@dataclass
class ProfileSettings(DataClassORJSONMixin):
    """Settings for a Charging location/Profile."""

    class Config(BaseConfig):
        """Configuration for serialization and deserialization.."""

        code_generation_options = [  # noqa: RUF012
            TO_DICT_ADD_BY_ALIAS_FLAG
        ]

    max_charging_current: MaxChargeCurrent = field(
        metadata=field_options(alias="maxChargingCurrent")
    )
    min_battery_state_of_charge: MinBatterySOC = field(
        metadata=field_options(alias="minBatteryStateOfCharge")
    )
    target_state_of_charge_in_percent: int = field(
        metadata=field_options(alias="targetStateOfChargeInPercent")
    )
    auto_unlock_plug_when_charged: PlugUnlockMode = field(
        metadata=field_options(alias="autoUnlockPlugWhenCharged")
    )


@dataclass
class ChargingTimers(DataClassORJSONMixin):
    """Timers for a Charging location."""

    id: int
    enabled: bool
    time: time
    type: TimerMode
    recurring_on: list[Weekday] = field(metadata=field_options(alias="recurringOn"))

    class Config(BaseConfig):
        """Configuration for serialization and deserialization.."""

        code_generation_options = [  # noqa: RUF012
            TO_DICT_ADD_BY_ALIAS_FLAG
        ]

    def __post_serialize__(self, d: dict[Any, Any]) -> dict[Any, Any]:
        """Post-process the data before serialization."""
        # Test for a specific member that is named differently when serializing by alias
        # so that we can match the HH:MM send by the Skoda servers then and only then,
        # as by_alias is not passed in the Context if used
        if self.time and "recurringOn" in d:
            d["time"] = self.time.strftime("%H:%M")  # Format to hh:mm
        return d


@dataclass
class ChargingProfile(DataClassORJSONMixin):
    """Charging profile definition."""

    id: int
    name: str
    settings: ProfileSettings
    preferred_charging_times: list[ChargingTimes] = field(
        metadata=field_options(alias="preferredChargingTimes")
    )
    timers: list[ChargingTimers]
    location: Coordinates | None = field(default=None)

    class Config(BaseConfig):
        """Configuration for serialization and deserialization.."""

        code_generation_options = [  # noqa: RUF012
            TO_DICT_ADD_BY_ALIAS_FLAG
        ]


@dataclass
class CurrentProfile(DataClassORJSONMixin):
    """Information on the currently active charging profile."""

    id: int
    name: str
    target_state_of_charge_in_percent: int = field(
        metadata=field_options(alias="targetStateOfChargeInPercent")
    )
    next_charging_time: time | None = field(
        default=None, metadata=field_options(alias="nextChargingTime")
    )


@dataclass
class ChargingProfiles(BaseResponse):
    """Information related to location bound charging settings for an EV."""

    charging_profiles: list[ChargingProfile] = field(
        metadata=field_options(alias="chargingProfiles")
    )
    current_vehicle_position_profile: CurrentProfile | None = field(
        default=None, metadata=field_options(alias="currentVehiclePositionProfile")
    )
    car_captured_timestamp: datetime | None = field(
        default=None, metadata=field_options(alias="carCapturedTimestamp")
    )
