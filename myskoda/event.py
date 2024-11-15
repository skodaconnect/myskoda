"""Events emitted by MySkoda."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal

from mashumaro.mixins.orjson import DataClassORJSONMixin

from .models.operation_request import OperationRequest
from .models.service_event import ServiceEvent, ServiceEventCharging


class ServiceEventTopic(StrEnum):
    ACCESS = "ACCESS"
    AIR_CONDITIONING = "AIR_CONDITIONING"
    CHARGING = "CHARGING"
    LIGHTS = "LIGHTS"
    DEPARTURE = "DEPARTURE"


class AccountEventTopic(StrEnum):
    ACCOUNT_PRIVACY = "ACCOUNT_PRIVACY"


class EventType(StrEnum):
    ACCOUNT_EVENT = "account-event"
    OPERATION = "operation-request"
    SERVICE_EVENT = "service-event"


@dataclass
class BaseEvent(DataClassORJSONMixin):
    vin: str
    user_id: str
    timestamp: datetime


@dataclass
class EventOperation(BaseEvent):
    operation: OperationRequest
    type: Literal[EventType.OPERATION] = EventType.OPERATION


@dataclass
class EventAirConditioning(BaseEvent):
    event: ServiceEvent
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.AIR_CONDITIONING] = ServiceEventTopic.AIR_CONDITIONING


@dataclass
class EventCharging(BaseEvent):
    event: ServiceEventCharging
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.CHARGING] = ServiceEventTopic.CHARGING


@dataclass
class EventAccess(BaseEvent):
    event: ServiceEvent
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.ACCESS] = ServiceEventTopic.ACCESS


@dataclass
class EventLights(BaseEvent):
    event: ServiceEvent
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.LIGHTS] = ServiceEventTopic.LIGHTS


@dataclass
class EventDeparture(BaseEvent):
    event: ServiceEvent
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.DEPARTURE] = ServiceEventTopic.DEPARTURE


@dataclass
class EventAccountPrivacy(BaseEvent):
    type: Literal[EventType.ACCOUNT_EVENT] = EventType.ACCOUNT_EVENT
    topic: Literal[AccountEventTopic.ACCOUNT_PRIVACY] = AccountEventTopic.ACCOUNT_PRIVACY


Event = (
    EventAccountPrivacy
    | EventOperation
    | EventAccess
    | EventAirConditioning
    | EventCharging
    | EventLights
    | EventDeparture
)
