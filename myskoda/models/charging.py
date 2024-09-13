from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any

from .common import ActiveState, EnabledState


class ChargeMode(str, Enum):
    MANUAL = "MANUAL"


class MaxChargeCurrent(str, Enum):
    MAXIMUM = "MAXIMUM"
    REDUCED = "REDUCED"


class ChargingState(str, Enum):
    READY_FOR_CHARGING = "READY_FOR_CHARGING"
    CONNECT_CABLE = "CONNECT_CABLE"
    CONSERVING = "CONSERVING"
    CHARGING = "CHARGING"


class ChargeType(str, Enum):
    AC = "AC"


class PlugUnlockMode(str, Enum):
    PERMANENT = "PERMANENT"
    ON = "ON"
    OFF = "OFF"


class Settings(BaseModel):
    available_charge_modes: list[ChargeMode] = Field(None, alias="availableChargeModes")
    battery_support: EnabledState = Field(None, alias="batterySupport")
    charging_care_mode: ActiveState = Field(None, alias="chargingCareMode")
    max_charge_current_ac: MaxChargeCurrent = Field(None, alias="maxChargeCurrentAc")
    preferred_charge_mode: ChargeMode = Field(None, alias="preferredChargeMode")
    target_state_of_charge_in_percent: int = Field(
        None, alias="targetStateOfChargeInPercent"
    )
    auto_unlock_plug_when_charged: PlugUnlockMode = Field(
        None, alias="autoUnlockPlugWhenCharged"
    )


class Battery(BaseModel):
    remaining_cruising_range_in_meters: int = Field(
        None, alias="remainingCruisingRangeInMeters"
    )
    state_of_charge_in_percent: int = Field(None, alias="stateOfChargeInPercent")


class Status(BaseModel):
    battery: Battery
    charge_power_in_kw: float | None = Field(None, alias="chargePowerInKw")
    charging_rate_in_kilometers_per_hour: float = Field(
        None, alias="chargingRateInKilometersPerHour"
    )
    remaining_time_to_fully_charged_in_minutes: int = Field(
        None, alias="remainingTimeToFullyChargedInMinutes"
    )
    state: ChargingState


class Charging(BaseModel):
    """Information related to charging an EV."""

    car_captured_timestamp: datetime = Field(None, alias="carCapturedTimestamp")
    errors: list[Any]
    is_vehicle_in_saved_location: bool = Field(None, alias="isVehicleInSavedLocation")
    settings: Settings
    status: Status
    charging_rate_in_kilometers_per_hour: float | None = Field(
        None, alias="chargingRateInKilometersPerHour"
    )
    remaining_time_to_fully_charged_in_minutes: int | None = Field(
        None, alias="remainingTimeToFullyChargedInMinutes"
    )
    charge_type: ChargeType | None = Field(None, alias="chargeType")
    charge_power_in_kw: float | None = Field(None, alias="chargePowerInKw")
