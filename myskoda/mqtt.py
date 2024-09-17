"""MQTT client module for the MySkoda server."""

import json
import logging
import re
import ssl
from asyncio import Future, get_event_loop
from collections.abc import Callable
from enum import StrEnum
from typing import Literal, cast

from asyncio_paho.client import AsyncioPahoClient
from paho.mqtt.client import MQTTMessage

from .const import (
    MQTT_ACCOUNT_EVENT_TOPICS,
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_OPERATION_TOPICS,
    MQTT_SERVICE_EVENT_TOPICS,
)
from .event import (
    Event,
    EventAccess,
    EventAccountPrivacy,
    EventAirConditioning,
    EventCharging,
    EventLights,
    EventOperation,
    EventType,
)
from .models.mqtt import OperationName, OperationRequest, OperationStatus
from .models.user import User
from .rest_api import RestApi

_LOGGER = logging.getLogger(__name__)
TOPIC_RE = re.compile("^(.*?)/(.*?)/(.*?)/(.*?)$")


class OperationListenerType(StrEnum):
    OPERATION_NAME = "OPERATION_NAME"
    TRACE_ID = "TRACE_ID"


class OperationListenerForName:
    type: Literal[OperationListenerType.OPERATION_NAME] = OperationListenerType.OPERATION_NAME
    operation_name: OperationName
    future: Future[OperationRequest]

    def __init__(  # noqa: D107
        self, operation_name: OperationName, future: Future[OperationRequest]
    ) -> None:
        self.operation_name = operation_name
        self.future = future


class OperationListenerForTraceId:
    type: Literal[OperationListenerType.TRACE_ID] = OperationListenerType.TRACE_ID
    trace_id: str
    future: Future[OperationRequest]

    def __init__(self, trace_id: str, future: Future[OperationRequest]) -> None:  # noqa: D107
        self.trace_id = trace_id
        self.future = future


OperationListener = OperationListenerForTraceId | OperationListenerForName


class MQTT:
    api: RestApi
    user: User
    vehicles: list[str]
    _callbacks: list[Callable[[Event], None]]
    _operation_listeners: list[OperationListener]
    client: AsyncioPahoClient

    def __init__(self, api: RestApi) -> None:  # noqa: D107
        self.api = api
        self._callbacks = []
        self._operation_listeners = []

    def subscribe(self, callback: Callable[[Event], None]) -> None:
        """Listen for events emitted by MySkoda's MQTT broker."""
        self._callbacks.append(callback)

    async def connect(self) -> None:
        """Connect to the MQTT broker and listen for messages."""
        _LOGGER.info(f"Connecting to MQTT on {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
        self.user = await self.api.get_user()
        _LOGGER.info(f"Using user id {self.user.id}...")
        self.vehicles = await self.api.list_vehicles()
        self.client = AsyncioPahoClient()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.tls_set_context(context=ssl.create_default_context())
        self.client.username_pw_set(
            self.user.id, await self.api.idk_session.get_access_token(self.api.session)
        )
        self.client.connect_async(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

    def disconnect(self) -> None:
        """Stop the thread for processing MQTT messages."""
        self.client.disconnect()  # pyright: ignore [reportArgumentType]

    def async_wait_for_next_operation(
        self, operation_name: OperationName
    ) -> Future[OperationRequest]:
        """Wait until the next operation of the specified type completes."""
        future: Future[OperationRequest] = get_event_loop().create_future()

        self._operation_listeners.append(OperationListenerForName(operation_name, future))

        return future

    def _on_connect(
        self, client: AsyncioPahoClient, _data: None, _flags: dict, _reason: int
    ) -> None:
        _LOGGER.info("MQTT Connected.")
        user_id = self.user.id

        for vin in self.vehicles:
            for topic in MQTT_OPERATION_TOPICS:
                client.subscribe(f"{user_id}/{vin}/operation-request/{topic}")
            for topic in MQTT_SERVICE_EVENT_TOPICS:
                client.subscribe(f"{user_id}/{vin}/service-event/{topic}")
            for topic in MQTT_ACCOUNT_EVENT_TOPICS:
                client.subscribe(f"{user_id}/{vin}/account-event/{topic}")

    def _emit(self, event: Event) -> None:
        for callback in self._callbacks:
            callback(event)

        self._handle_operation(event)

    def _handle_operation_in_progress(self, operation: OperationRequest) -> None:
        listeners = self._operation_listeners
        self._operation_listeners = []
        for listener in listeners:
            if (
                listener.type != OperationListenerType.OPERATION_NAME
                or listener.operation_name != operation.operation
            ):
                self._operation_listeners.append(listener)
                continue
            _LOGGER.debug(
                "Converting listener for operation name '%s' to trace '%s'.",
                operation.operation,
                operation.trace_id,
            )
            self._operation_listeners.append(
                OperationListenerForTraceId(operation.trace_id, listener.future)
            )

    def _handle_operation_completed(self, operation: OperationRequest) -> None:
        listeners = self._operation_listeners
        self._operation_listeners = []
        for listener in listeners:
            if (
                listener.type != OperationListenerType.TRACE_ID
                or listener.trace_id != operation.trace_id
            ):
                self._operation_listeners.append(listener)
                continue
            _LOGGER.debug("Resolving listener for trace id '%s'.", operation.trace_id)
            listener.future.set_result(operation)

    def _handle_operation(self, event: Event) -> None:
        if event.type != EventType.OPERATION:
            return

        if event.operation.status == OperationStatus.IN_PROGRESS:
            _LOGGER.debug(
                "An operation '%s' is now in progress. Trace id: %s",
                event.operation.operation,
                event.operation.trace_id,
            )
            self._handle_operation_in_progress(event.operation)
            return

        _LOGGER.debug(
            "Operation '%s' for trace id '%s' completed.",
            event.operation.operation,
            event.operation.trace_id,
        )
        self._handle_operation_completed(event.operation)

    def _on_message(self, _client: AsyncioPahoClient, _data: None, msg: MQTTMessage) -> None:
        # Extract the topic, user id and vin from the topic's name.
        # Internally, the topic will always look like this:
        # `/{user_id}/{vin}/path/to/topic`
        topic_match = TOPIC_RE.match(msg.topic)
        if not topic_match:
            _LOGGER.warning("Unexpected MQTT topic encountered: %s", topic_match)
            return

        [user_id, vin, event_type, topic] = topic_match.groups()
        event_type = EventType(event_type)

        # Cast the data from binary string, ignoring empty messages.
        data = cast(str, msg.payload)
        if len(data) == 0:
            return

        _LOGGER.debug("Message (%s) received for %s on topic %s: %s", event_type, vin, topic, data)

        # Messages will contain payload as JSON.
        data = json.loads(msg.payload)

        match event_type:
            case EventType.OPERATION:
                self._emit(EventOperation(vin, user_id, data))
            case EventType.ACCOUNT_EVENT:
                self._emit(EventAccountPrivacy(vin, user_id, data))
            case EventType.SERVICE_EVENT:
                match topic:
                    case "air-conditioning":
                        self._emit(EventAirConditioning(vin, user_id, data))
                    case "charging":
                        self._emit(EventCharging(vin, user_id, data))
                    case "vehicle-status/access":
                        self._emit(EventAccess(vin, user_id, data))
                    case "vehicle-status/lights":
                        self._emit(EventLights(vin, user_id, data))


class OperationFailedError(Exception):
    def __init__(self, operation: OperationRequest) -> None:  # noqa: D107
        op = operation.operation
        error = operation.error_code
        trace = operation.trace_id
        super().__init__(f"Operation {op} with trace {trace} failed: {error}")
