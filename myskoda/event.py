"""Events emitted by MySkoda."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from .models.operation_request import OperationRequest
from .models.service_event import ServiceEvent, ServiceEventCharging


class ServiceEventTopic(StrEnum):
    ACCESS = "ACCESS"
    AIR_CONDITIONING = "AIR_CONDITIONING"
    CHARGING = "CHARGING"
    LIGHTS = "LIGHTS"


class AccountEventTopic(StrEnum):
    ACCOUNT_PRIVACY = "ACCOUNT_PRIVACY"


class EventType(StrEnum):
    ACCOUNT_EVENT = "account-event"
    OPERATION = "operation-request"
    SERVICE_EVENT = "service-event"


class BaseEvent:
    vin: str
    user_id: str
    timestamp: datetime

    def __init__(self, vin: str, user_id: str) -> None:  # noqa: D107
        self.vin = vin
        self.user_id = user_id
        self.timestamp = datetime.now(tz=UTC)


class EventOperation(BaseEvent):
    type: Literal[EventType.OPERATION] = EventType.OPERATION
    operation: OperationRequest

    def __init__(self, vin: str, user_id: str, operation: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.operation = OperationRequest.from_dict(operation)


class EventAirConditioning(BaseEvent):
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.AIR_CONDITIONING] = ServiceEventTopic.AIR_CONDITIONING
    event: ServiceEvent

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.event = ServiceEvent.from_dict(payload)


class EventCharging(BaseEvent):
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.CHARGING] = ServiceEventTopic.CHARGING
    event: ServiceEventCharging

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.event = ServiceEventCharging.from_dict(payload)


class EventAccess(BaseEvent):
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.ACCESS] = ServiceEventTopic.ACCESS
    event: ServiceEvent

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.event = ServiceEvent.from_dict(payload)


class EventLights(BaseEvent):
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.LIGHTS] = ServiceEventTopic.LIGHTS
    event: ServiceEvent

    def __init__(self, vin: str, user_id: str, payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)
        self.event = ServiceEvent.from_dict(payload)


class EventAccountPrivacy(BaseEvent):
    type: Literal[EventType.ACCOUNT_EVENT] = EventType.ACCOUNT_EVENT
    topic: Literal[AccountEventTopic.ACCOUNT_PRIVACY] = AccountEventTopic.ACCOUNT_PRIVACY

    def __init__(self, vin: str, user_id: str, _payload: dict) -> None:  # noqa: D107
        super().__init__(vin, user_id)


Event = (
    EventAccountPrivacy
    | EventOperation
    | EventAccess
    | EventAirConditioning
    | EventCharging
    | EventLights
)
