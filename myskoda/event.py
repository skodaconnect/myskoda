"""Events emitted by MySkoda."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from .models.mqtt import OperationRequest, ServiceEvent, ServiceEventCharging


class EventName(StrEnum):
    ACCESS = "ACCESS"
    ACCOUNT_PRIVACY = "ACCOUNT_PRIVACY"
    AIR_CONDITIONING = "AIR_CONDITIONING"
    APPLY_BACKUP = "APPLY_BACKUP"
    CHARGING = "CHARGING"
    HONK_AND_FLASH = "HONK_AND_FLASH"
    LIGHTS = "LIGHTS"
    LOCK_VEHICLE = "LOCK_VEHICLE"
    SET_TARGET_TEMPERATURE = "SET_TARGET_TEMPERATURE"
    START_STOP_AIR_CONDITIONING = "START_STOP_AIR_CONDITIONING"
    START_STOP_CHARGING = "START_STOP_CHARGING"
    START_STOP_WINDOW_HEATING = "START_STOP_WINDOW_HEATING"
    UPDATE_BATTERY_SUPPORT = "UPDATE_BATTERY_SUPPORT"
    WAKEUP = "WAKEUP"


class BaseEvent:
    vin: str
    user_id: str
    timestamp: datetime

    def __init__(self, vin: str, user_id: str) -> None:  # noqa: D107
        self.vin = vin
        self.user_id = user_id
        self.timestamp = datetime.now(tz=UTC)


class EventUpdateBatterySupport(BaseEvent):
    name: Literal[EventName.UPDATE_BATTERY_SUPPORT]
    payload: OperationRequest

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.UPDATE_BATTERY_SUPPORT
        self.payload = OperationRequest(**payload)


class EventLockVehicle(BaseEvent):
    name: Literal[EventName.LOCK_VEHICLE]
    payload: OperationRequest

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.LOCK_VEHICLE
        self.payload = OperationRequest(**payload)


class EventWakeup(BaseEvent):
    name: Literal[EventName.WAKEUP]
    payload: OperationRequest

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.WAKEUP
        self.payload = OperationRequest(**payload)


class EventSetTargetTemperature(BaseEvent):
    name: Literal[EventName.SET_TARGET_TEMPERATURE]
    payload: OperationRequest

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.SET_TARGET_TEMPERATURE
        self.payload = OperationRequest(**payload)


class EventStartStopAirConditioning(BaseEvent):
    name: Literal[EventName.START_STOP_AIR_CONDITIONING]
    payload: OperationRequest

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.START_STOP_AIR_CONDITIONING
        self.payload = OperationRequest(**payload)


class EventStartStopWindowHeating(BaseEvent):
    name: Literal[EventName.START_STOP_WINDOW_HEATING]
    payload: OperationRequest

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.START_STOP_WINDOW_HEATING
        self.payload = OperationRequest(**payload)


class EventStartStopCharging(BaseEvent):
    name: Literal[EventName.START_STOP_CHARGING]
    payload: OperationRequest

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.START_STOP_CHARGING
        self.payload = OperationRequest(**payload)


class EventHonkAndFlash(BaseEvent):
    name: Literal[EventName.HONK_AND_FLASH]
    payload: OperationRequest

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.HONK_AND_FLASH
        self.payload = OperationRequest(**payload)


class EventApplyBackup(BaseEvent):
    name: Literal[EventName.APPLY_BACKUP]
    payload: OperationRequest

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.APPLY_BACKUP
        self.payload = OperationRequest(**payload)


class EventAirConditioning(BaseEvent):
    name: Literal[EventName.AIR_CONDITIONING]
    payload: ServiceEvent

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.AIR_CONDITIONING
        self.payload = ServiceEvent(**payload)


class EventCharging(BaseEvent):
    name: Literal[EventName.CHARGING]
    payload: ServiceEventCharging

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.CHARGING
        self.payload = ServiceEventCharging(**payload)


class EventAccess(BaseEvent):
    name: Literal[EventName.ACCESS]
    payload: ServiceEvent

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.ACCESS
        self.payload = ServiceEvent(**payload)


class EventLights(BaseEvent):
    name: Literal[EventName.LIGHTS]
    payload: ServiceEvent

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.LIGHTS
        self.payload = ServiceEvent(**payload)


class EventAccountPrivacy(BaseEvent):
    name: Literal[EventName.ACCOUNT_PRIVACY]

    def __init__(self, vin: str, user_id: str, _payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.name = EventName.ACCOUNT_PRIVACY


Event = (
    EventAccess
    | EventAccountPrivacy
    | EventAirConditioning
    | EventApplyBackup
    | EventApplyBackup
    | EventCharging
    | EventHonkAndFlash
    | EventLights
    | EventLockVehicle
    | EventSetTargetTemperature
    | EventStartStopAirConditioning
    | EventStartStopCharging
    | EventStartStopWindowHeating
    | EventUpdateBatterySupport
    | EventWakeup
)
