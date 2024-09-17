"""Models relaterd to the MQTT API."""

from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, validator


class OperationStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_WARNING = "COMPLETED_WARNING"
    ERROR = "ERROR"


class OperationName(StrEnum):
    APPLY_BACKUP = "apply-backup"
    LOCK = "lock"
    SET_AIR_CONDITIONING_AT_UNLOCK = "set-air-conditioning-at-unlock"
    SET_AIR_CONDITIONING_SEATS_HEATING = "set-air-conditioning-seats-heating"
    SET_AIR_CONDITIONING_TARGET_TEMPERATURE = "set-air-conditioning-target-temperature"
    SET_AIR_CONDITIONING_TIMERS = "set-air-conditioning-timers"
    SET_AIR_CONDITIONING_WITHOUT_EXTERNAL_POWER = (
        "set-air-conditioning-without-external-power"
    )
    SET_CLIMATE_PLANS = "set-climate-plans"
    START_ACTIVE_VENTILATION = "start-active-ventilation"
    START_AIR_CONDITIONING = "start-air-conditioning"
    START_AUXILIARY_HEATING = "start-auxiliary-heating"
    START_CHARGING = "start-charging"
    START_FLASH = "start-flash"
    START_HONK = "start-honk"
    START_STOP_CHARGING = "start-stop-charging"
    STOP_ACTIVE_VENTILATION = "stop-active-ventilation"
    STOP_AIR_CONDITIONING = "stop-air-conditioning"
    STOP_AUXILIARY_HEATING = "stop-auxiliary-heating"
    STOP_CHARGING = "stop-charging"
    STOP_WINDOW_HEATING = "stop-window-heating"
    UNLOCK = "unlock"
    UPDATE_AUTO_UNLOCK_PLUG = "update-auto-unlock-plug"
    UPDATE_BATTERY_SUPPORT = "update-battery-support"
    UPDATE_CARE_MODE = "update-care-mode"
    UPDATE_CHARGE_LIMIT = "update-charge-limit"
    UPDATE_CHARGE_MODE = "update-charge-mode"
    UPDATE_CHARGING_CURRENT = "update-charging-current"
    UPDATE_CHARGING_PROFILES = "update-charging-profiles"
    UPDATE_DEPARTURE_TIMERS = "update-departure-timers"
    UPDATE_MINIMAL_SOC = "update-minimal-soc"
    UPDATE_TARGET_TEMPERATURE = "update-target-temperature"
    WAKEUP = "wakeup"
    WINDOWS_HEATING = "windows-heating"


class ServiceEventName(StrEnum):
    CHANGE_SOC = "change-soc"
    CHANGE_ACCESS = "change-access"
    CHANGE_LIGHTS = "change-lights"
    CLIMATISATION_COMPLETED = "climatisation-completed"
    CHANGE_REMAINING_TIME = "change-remaining-time"
    CHANGE_CHARGE_MODE = "change-charge-mode"


class OperationRequest(BaseModel):
    version: int
    trace_id: str = Field(None, alias="traceId")
    request_id: str = Field(None, alias="requestId")
    operation: OperationName
    status: OperationStatus
    error_code: str = Field(None, alias="errorCode")


class ServiceEventData(BaseModel):
    user_id: str = Field(None, alias="userId")
    vin: str


T = TypeVar("T", bound=ServiceEventData)


class ServiceEvent(BaseModel, Generic[T]):
    version: int
    trace_id: str = Field(None, alias="traceId")
    timestamp: datetime = Field(None, alias="requestId")
    producer: str
    name: ServiceEventName
    data: T


class ServiceEventChargingState(StrEnum):
    CHARGING = "charging"
    CHARGED_NOT_CONSERVING = "chargePurposeReachedAndNotConservationCharging"
    NOT_READY = "notReadyForCharging"
    READY = "readyForCharging"


class ServiceEventChargingData(ServiceEventData):
    mode: str
    state: ServiceEventChargingState
    soc: int
    charged_range: str = Field(None, alias="chargedRange")
    time_to_finish: str | None = Field(None, alias="timeToFinish")

    @validator("soc")
    def _parse_soc(cls, value: str) -> int:  # noqa: N805
        return int(value)

    @validator("charged_range")
    def _parse_charged_range(cls, value: str) -> int:  # noqa: N805
        return int(value)

    @validator("time_to_finish")
    def _parse_time_to_finish(cls, value: str) -> int | None:  # noqa: N805
        if value == "null":
            return None
        return int(value)


class ServiceEventCharging(ServiceEvent):
    data: ServiceEventChargingData
