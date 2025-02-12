"""Events emitted by MySkoda."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal

from mashumaro.mixins.orjson import DataClassORJSONMixin

from .models.operation_request import OperationRequest
from .models.service_event import ServiceEvent
from .models.vehicle_event import VehicleEvent


class ServiceEventTopic(StrEnum):
    ACCESS = "ACCESS"
    AIR_CONDITIONING = "AIR_CONDITIONING"
    AUXILIARY_HEATING = "AUXILIARY_HEATING"
    CHARGING = "CHARGING"
    LIGHTS = "LIGHTS"
    DEPARTURE = "DEPARTURE"
    ODOMETER = "ODOMETER"


class VehicleEventTopic(StrEnum):
    VEHICLE_CONNECTION_STATUS_UPDATE = "VEHICLE_CONNECTION_STATUS_UPDATE"
    VEHICLE_IGNITION_STATUS = "VEHICLE_IGNITION_STATUS"


class AccountEventTopic(StrEnum):
    ACCOUNT_PRIVACY = "ACCOUNT_PRIVACY"


class EventType(StrEnum):
    ACCOUNT_EVENT = "account-event"
    OPERATION = "operation-request"
    SERVICE_EVENT = "service-event"
    VEHICLE_EVENT = "vehicle-event"


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
class EventAuxiliaryHeating(BaseEvent):
    event: ServiceEvent
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.AUXILIARY_HEATING] = ServiceEventTopic.AUXILIARY_HEATING


@dataclass
class EventCharging(BaseEvent):
    event: ServiceEvent
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
class EventOdometer(BaseEvent):
    event: ServiceEvent
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.ODOMETER] = ServiceEventTopic.ODOMETER


@dataclass
class EventDeparture(BaseEvent):
    event: ServiceEvent
    type: Literal[EventType.SERVICE_EVENT] = EventType.SERVICE_EVENT
    topic: Literal[ServiceEventTopic.DEPARTURE] = ServiceEventTopic.DEPARTURE


@dataclass
class EventAccountPrivacy(BaseEvent):
    type: Literal[EventType.ACCOUNT_EVENT] = EventType.ACCOUNT_EVENT
    topic: Literal[AccountEventTopic.ACCOUNT_PRIVACY] = AccountEventTopic.ACCOUNT_PRIVACY


@dataclass
class EventVehicleIgnitionStatus(BaseEvent):
    event: VehicleEvent
    type: Literal[EventType.VEHICLE_EVENT] = EventType.VEHICLE_EVENT
    topic: Literal[VehicleEventTopic.VEHICLE_IGNITION_STATUS] = (
        VehicleEventTopic.VEHICLE_IGNITION_STATUS
    )


@dataclass
class EventVehicleConnectionStatusUpdate(BaseEvent):
    event: VehicleEvent
    type: Literal[EventType.VEHICLE_EVENT] = EventType.VEHICLE_EVENT
    topic: Literal[VehicleEventTopic.VEHICLE_CONNECTION_STATUS_UPDATE] = (
        VehicleEventTopic.VEHICLE_CONNECTION_STATUS_UPDATE
    )


Event = (
    EventAccountPrivacy
    | EventOperation
    | EventAccess
    | EventAirConditioning
    | EventAuxiliaryHeating
    | EventCharging
    | EventLights
    | EventOdometer
    | EventDeparture
    | EventVehicleIgnitionStatus
    | EventVehicleConnectionStatusUpdate
)
