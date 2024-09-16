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


class OperationRequest(BaseModel):
    version: int
    trace_id: str = Field(None, alias="traceId")
    request_id: str = Field(None, alias="requestId")
    operation: str
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
    name: str
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


ServiceEventCharging = ServiceEvent[ServiceEventChargingData]
