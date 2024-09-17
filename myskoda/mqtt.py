"""MQTT client module for the MySkoda server."""

import json
import logging
import re
import ssl
from asyncio import Future, get_running_loop
from collections.abc import Callable
from typing import cast

from paho.mqtt.client import Client, MQTTMessage

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
from .models.mqtt import OperationRequest, OperationStatus
from .models.user import User
from .rest_api import RestApi

_LOGGER = logging.getLogger(__name__)
TOPIC_RE = re.compile("^(.*?)/(.*?)/(.*?)/(.*?)$")


class MQTT:
    api: RestApi
    user: User
    vehicles: list[str]
    _callbacks: list[Callable[[Event], None]]
    _trace_callbacks: dict[str, list[Future[OperationRequest]]]

    def __init__(self, api: RestApi) -> None:  # noqa: D107
        self.api = api
        self._callbacks = []
        self._trace_callbacks = {}

    def subscribe(self, callback: Callable[[Event], None]) -> None:
        """Listen for events emitted by MySkoda's MQTT broker."""
        self._callbacks.append(callback)

    async def connect(self) -> None:
        """Connect to the MQTT broker and listen for messages."""
        _LOGGER.info(f"Connecting to MQTT on {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
        self.user = await self.api.get_user()
        _LOGGER.info(f"Using user id {self.user.id}...")
        self.vehicles = await self.api.list_vehicles()
        self.client = Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.tls_set_context(context=ssl.create_default_context())
        self.client.username_pw_set(
            self.user.id, await self.api.idk_session.get_access_token(self.api.session)
        )
        self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

    def loop_forever(self) -> None:
        """Make the MQTT client process new messages until the current process is cancelled."""
        self.client.loop_forever()

    def loop_start(self) -> None:
        """Make the MQTT client process new messages in a thread in the background."""
        self.client.loop_start()

    def loop_stop(self) -> None:
        """Stop the thread for processing MQTT messages."""
        self.client.loop_stop()

    def _add_trace_future(
        self, trace_id: str, future: Future[OperationRequest]
    ) -> None:
        if trace_id not in self._trace_callbacks:
            self._trace_callbacks[trace_id] = []
        self._trace_callbacks[trace_id].append(future)

    async def wait_for_operation(self, trace_id: str) -> None:
        """Wait until the operation with the specified trace id completes."""
        future: Future[OperationRequest] = get_running_loop().create_future()
        self._add_trace_future(trace_id, future)

        operation = await future

        if operation.status == OperationStatus.ERROR:
            raise OperationFailedError(operation)

        if operation.status == OperationStatus.COMPLETED_WARNING:
            _LOGGER.warning(
                "Operation %s for trace %s completed with warnings.",
                operation.operation,
                operation.trace_id,
            )

    def _on_connect(
        self, client: Client, _data: None, _flags: dict, _reason: int
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

    def _handle_operation(self, event: Event) -> None:
        if event.type != EventType.OPERATION:
            return

        if event.operation.status == OperationStatus.IN_PROGRESS:
            return

        _LOGGER.debug(
            "Operation '%s' for trace id '%s' completed.",
            event.operation.operation,
            event.operation.trace_id,
        )

        if event.operation.trace_id not in self._trace_callbacks:
            return

        futures = self._trace_callbacks[event.operation.trace_id]

        _LOGGER.debug(
            "Resolving %d listener(s) for trace id '%s' with status '%s'.",
            len(futures),
            event.operation.trace_id,
            event.operation.status,
        )
        for future in futures:
            future.set_result(event.operation)

        del self._trace_callbacks[event.operation.trace_id]

    def _on_message(self, _client: Client, _data: None, msg: MQTTMessage) -> None:
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

        _LOGGER.debug("Message received for %s (%s): %s", vin, topic, data)

        # Messages will contain payload as JSON.
        data = json.loads(msg.payload)

        match event_type:
            case EventType.OPERATION:
                self._emit(EventOperation(vin, user_id, data))
            case EventType.ACCOUNT_EVENT:
                self._emit(EventAccountPrivacy(vin, user_id, data))
            case EventType.SERVICE_EVENT:
                match topic:
                    case "service-event/air-conditioning":
                        self._emit(EventAirConditioning(vin, user_id, data))
                    case "service-event/charging":
                        self._emit(EventCharging(vin, user_id, data))
                    case "service-event/vehicle-status/access":
                        self._emit(EventAccess(vin, user_id, data))
                    case "service-event/vehicle-status/lights":
                        self._emit(EventLights(vin, user_id, data))


class OperationFailedError(Exception):
    def __init__(self, operation: OperationRequest) -> None:  # noqa: D107
        op = operation.operation
        error = operation.error_code
        trace = operation.trace_id
        super().__init__(f"Operation {op} with trace {trace} failed: {error}")
