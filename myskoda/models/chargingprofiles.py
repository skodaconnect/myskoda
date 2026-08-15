"""Models for responses of api/v1/charging/vin/profiles endpoint."""

from dataclasses import dataclass, field
from datetime import time
from typing import Any
from tribool import Tribool

from mashumaro import field_options
from mashumaro.config import (
    TO_DICT_ADD_BY_ALIAS_FLAG,
    BaseConfig,
)
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.types import SerializationStrategy

from .air_conditioning import TimerMode
from .charging import MaxChargeCurrent, PlugUnlockMode
from .common import BaseResponse, Coordinates, Weekday


class FormattedTribool(SerializationStrategy):
    """Tribool serialization strategy for use with mashumaro."""
    def serialize(self, value: Tribool) -> bool | None:
        """Serialize Tribool to True, False, None"""
        return value.value

    def deserialize(self, value: bool | None) -> Tribool:
        """Deserialize Tribool from True, False or None"""
        return Tribool(value)


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
    start_climatisation: Tribool = field(
        default=Tribool(None),
        metadata=field_options(
            alias="startClimatisation", serialization_strategy=FormattedTribool()
        ),
    )
    one_off_day: Weekday | None = field(default=None, metadata=field_options(alias="oneOffDay"))
    recurring_on: list[Weekday] | None = field(
        default=None, metadata=field_options(alias="recurringOn")
    )

    class Config(BaseConfig):
        """Configuration for serialization and deserialization.."""

        omit_none = True
        code_generation_options = [  # noqa: RUF012
            TO_DICT_ADD_BY_ALIAS_FLAG
        ]

    def __post_serialize__(self, d: dict[Any, Any]) -> dict[Any, Any]:
        """Post-process the data before serialization."""
        # mashumaro's omit_default codegen builds an eval-able literal from repr() of the
        # default value. Tribool is a tuple subclass, so it takes that path, but the
        # generated code never imports `Tribool`, causing a NameError. Omit it manually
        # instead of relying on Config.omit_default for this field.
        if self.start_climatisation.value is None:
            d.pop("startClimatisation", None)
            d.pop("start_climatisation", None)

        # Test for a specific member that is named differently when serializing by alias
        # so that we can match the HH:MM send by the Skoda servers then and only then,
        # as by_alias is not passed in the Context if used
        if self.time and ("recurringOn" in d or "oneOffDay" in d):
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
