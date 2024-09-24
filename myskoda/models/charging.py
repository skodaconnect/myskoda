"""Models for responses of api/v1/charging endpoint."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import ActiveState, EnabledState


class ChargingErrorType(StrEnum):
    CARE_MODE_IS_NOT_AVAILABLE = "CARE_MODE_IS_NOT_AVAILABLE"
    AUTO_UNLOCK_IS_NOT_AVAILABLE = "AUTO_UNLOCK_IS_NOT_AVAILABLE"
    MAX_CHARGE_CURRENT_IS_NOT_AVAILABLE = "MAX_CHARGE_CURRENT_IS_NOT_AVAILABLE"
    CHARGE_LIMIT_IS_NOT_AVAILABLE = "CHARGE_LIMIT_IS_NOT_AVAILABLE"
    STATUS_OF_CHARGING_NOT_AVAILABLE = "STATUS_OF_CHARGING_NOT_AVAILABLE"
    STATUS_OF_CONNECTION_NOT_AVAILABLE = "STATUS_OF_CONNECTION_NOT_AVAILABLE"


@dataclass
class ChargingError(DataClassORJSONMixin):
    type: ChargingErrorType
    description: str


class ChargeMode(StrEnum):
    HOME_STORAGE_CHARGING = "HOME_STORAGE_CHARGING"
    IMMEDIATE_DISCHARGING = "IMMEDIATE_DISCHARGING"
    ONLY_OWN_CURRENT = "ONLY_OWN_CURRENT"
    PREFERRED_CHARGING_TIMES = "PREFERRED_CHARGING_TIMES"
    TIMER_CHARGING_WITH_CLIMATISATION = "TIMER_CHARGING_WITH_CLIMATISATION"
    TIMER = "TIMER"
    MANUAL = "MANUAL"
    OFF = "OFF"


class MaxChargeCurrent(StrEnum):
    MAXIMUM = "MAXIMUM"
    REDUCED = "REDUCED"


class ChargingState(StrEnum):
    READY_FOR_CHARGING = "READY_FOR_CHARGING"
    CONNECT_CABLE = "CONNECT_CABLE"
    CONSERVING = "CONSERVING"
    CHARGING = "CHARGING"


class ChargeType(StrEnum):
    AC = "AC"
    DC = "DC"


class PlugUnlockMode(StrEnum):
    PERMANENT = "PERMANENT"
    ON = "ON"
    OFF = "OFF"


@dataclass
class Settings(DataClassORJSONMixin):
    available_charge_modes: list[ChargeMode] = field(
        metadata=field_options(alias="availableChargeModes")
    )
    battery_support: EnabledState = field(metadata=field_options(alias="batterySupport"))
    charging_care_mode: ActiveState = field(metadata=field_options(alias="chargingCareMode"))
    max_charge_current_ac: MaxChargeCurrent = field(
        metadata=field_options(alias="maxChargeCurrentAc")
    )
    preferred_charge_mode: ChargeMode = field(metadata=field_options(alias="preferredChargeMode"))
    target_state_of_charge_in_percent: int = field(
        metadata=field_options(alias="targetStateOfChargeInPercent")
    )
    auto_unlock_plug_when_charged: PlugUnlockMode = field(
        metadata=field_options(alias="autoUnlockPlugWhenCharged")
    )


@dataclass
class Battery(DataClassORJSONMixin):
    remaining_cruising_range_in_meters: int = field(
        metadata=field_options(alias="remainingCruisingRangeInMeters")
    )
    state_of_charge_in_percent: int = field(metadata=field_options(alias="stateOfChargeInPercent"))


@dataclass
class ChargingStatus(DataClassORJSONMixin):
    battery: Battery
    state: ChargingState
    charging_rate_in_kilometers_per_hour: float = field(
        metadata=field_options(alias="chargingRateInKilometersPerHour")
    )
    remaining_time_to_fully_charged_in_minutes: int = field(
        metadata=field_options(alias="remainingTimeToFullyChargedInMinutes")
    )
    charge_power_in_kw: float | None = field(
        default=None, metadata=field_options(alias="chargePowerInKw")
    )
    charge_type: ChargeType | None = field(default=None, metadata=field_options(alias="chargeType"))


@dataclass
class Charging(DataClassORJSONMixin):
    """Information related to charging an EV."""

    errors: list[ChargingError]
    settings: Settings
    status: ChargingStatus | None
    car_captured_timestamp: datetime = field(metadata=field_options(alias="carCapturedTimestamp"))
    is_vehicle_in_saved_location: bool = field(
        metadata=field_options(alias="isVehicleInSavedLocation")
    )
