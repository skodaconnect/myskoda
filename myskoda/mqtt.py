"""MQTT client module for the MySkoda server."""

import logging
import re
import ssl
from asyncio import Future, Lock, create_task, get_event_loop, sleep
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, cast

from asyncio_paho.client import AsyncioPahoClient
from paho.mqtt.client import MQTTMessage

from myskoda.auth.authorization import Authorization
from myskoda.models.service_event import ServiceEvent, ServiceEventCharging

from .const import (
    MQTT_ACCOUNT_EVENT_TOPICS,
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_KEEPALIVE,
    MQTT_OPERATION_TOPICS,
    MQTT_RECONNECT_DELAY,
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
from .models.operation_request import OperationName, OperationRequest, OperationStatus

_LOGGER = logging.getLogger(__name__)
TOPIC_RE = re.compile("^(.*?)/(.*?)/(.*?)/(.*?)$")

background_tasks = set()


class OperationListener:
    operation_name: OperationName
    future: Future[OperationRequest]

    def __init__(  # noqa: D107
        self, operation_name: OperationName, future: Future[OperationRequest]
    ) -> None:
        self.operation_name = operation_name
        self.future = future


connect_lock = Lock()


class Mqtt:
    user_id: str | None
    vehicles: list[str] | None
    client: AsyncioPahoClient
    _callbacks: list[Callable[[Event], None | Awaitable[None]]]
    _operation_listeners: list[OperationListener]
    _connected_listeners: list[Future[None]]
    _subscribed_listeners: Future[None] | None
    _disconnect_listener: Future[None] | None
    should_reconnect: bool
    is_connected: bool
    authorization: Authorization
    host: str
    port: int
    enable_ssl: bool

    def __init__(  # noqa: D107
        self,
        authorization: Authorization,
        ssl_context: ssl.SSLContext | None = None,
        host: str = MQTT_BROKER_HOST,
        port: int = MQTT_BROKER_PORT,
        enable_ssl: bool = True,
    ) -> None:
        self.authorization = authorization
        self._callbacks = []
        self._operation_listeners = []
        self._connected_listeners = []
        self._subscribed_listener = None
        self._disconnect_listener = None
        self.ssl_context = ssl_context
        self.is_connected = False
        self.user_id = None
        self.vehicles = None
        self.host = host
        self.port = port
        self.enable_ssl = enable_ssl

    def subscribe(self, callback: Callable[[Event], None | Awaitable[None]]) -> None:
        """Listen for events emitted by MySkoda's MQTT broker."""
        self._callbacks.append(callback)

    async def _perform_connect(self) -> bool:
        """Connect to the MQTT broker once.

        Will return `True` if the connection was established and `False` otherwise.
        """
        try:
            if self.is_connected:
                return True

            _LOGGER.debug("Connecting to MQTT on %s:%d...", self.host, self.port)

            self.should_reconnect = True

            self.client = AsyncioPahoClient()
            self.client.enable_logger()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe
            self.client.on_disconnect = self._on_disconnect
            self.client.on_socket_close = self._on_socket_close
            self.client.on_connect_fail = self._on_connect_fail
            if self.enable_ssl:
                if self.ssl_context is not None:
                    self.client.tls_set_context(context=self.ssl_context)
                else:
                    self.client.tls_set_context(context=ssl.create_default_context())

            self.client.username_pw_set(
                self.user_id,
                await self.authorization.get_access_token(),
            )
            self.client.connect_async(self.host, self.port, MQTT_KEEPALIVE)

            await self._wait_for_connection()
        except FailedToConnectError:
            return False
        else:
            return True

    async def connect(self, user_id: str, vehicles: list[str]) -> None:
        """Connect to the MQTT broker and listen for messages."""
        self.user_id = user_id
        self.vehicles = vehicles
        async with connect_lock:
            while not await self._perform_connect():  # noqa: ASYNC110
                await sleep(MQTT_RECONNECT_DELAY)

        user_id = self.user_id

        for vin in self.vehicles:
            for topic in MQTT_OPERATION_TOPICS:
                await self._subscribe_to_topic(f"{user_id}/{vin}/operation-request/{topic}")
            for topic in MQTT_SERVICE_EVENT_TOPICS:
                await self._subscribe_to_topic(f"{user_id}/{vin}/service-event/{topic}")
            for topic in MQTT_ACCOUNT_EVENT_TOPICS:
                await self._subscribe_to_topic(f"{user_id}/{vin}/account-event/{topic}")

    def reconnect(self) -> None:
        """Reconnect a client that was previously connected and was disconnected."""
        _LOGGER.debug("Scheduling to reconnect MQTT.")

        if not self.should_reconnect:
            return

        if not self.user_id or not self.vehicles:
            raise NotConnectedError

        task = create_task(cast(Any, self.connect(self.user_id, self.vehicles)))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    async def disconnect(self) -> None:
        """Stop the thread for processing MQTT messages."""
        future: Future[None] = get_event_loop().create_future()
        self._disconnect_listener = future
        self.should_reconnect = False
        self.client.disconnect()  # pyright: ignore [reportArgumentType]
        await future
        self._disconnect_listener = None

    def _wait_for_connection(self) -> Future[None]:
        """Wait until MQTT is connected and setup."""
        future: Future[None] = get_event_loop().create_future()

        self._connected_listeners.append(future)

        return future

    def wait_for_operation(self, operation_name: OperationName) -> Future[OperationRequest]:
        """Wait until the next operation of the specified type completes."""
        _LOGGER.debug("Waiting for operation %s complete.", operation_name)
        future: Future[OperationRequest] = get_event_loop().create_future()

        self._operation_listeners.append(OperationListener(operation_name, future))

        return future

    def _on_socket_close(self, client: AsyncioPahoClient, _data: None, _socket: None) -> None:
        if client is not self.client:
            return
        _LOGGER.debug("Socket to MQTT broker closed.")
        self.is_connected = False
        if self._disconnect_listener is not None:
            self._disconnect_listener.set_result(None)
        self.reconnect()

    def _on_connect_fail(self, client: AsyncioPahoClient, _data: None) -> None:
        if client is not self.client:
            return
        _LOGGER.error("Failed to connect to MQTT.")
        for future in self._connected_listeners:
            future.set_exception(FailedToConnectError)
        self._connected_listeners = []

    def _on_disconnect(
        self,
        client: AsyncioPahoClient,
        _userdata: None,
        reason_code: int,
    ) -> None:
        if client is not self.client:
            return
        _LOGGER.debug("Connection to MQTT broker lost, reason %d.", reason_code)
        self.is_connected = False
        self.reconnect()

    def _on_connect(
        self, client: AsyncioPahoClient, _data: None, _flags: dict, _reason: int
    ) -> None:
        if client is not self.client:
            return

        self.is_connected = True

        _LOGGER.debug("MQTT Connected.")
        if not self.user_id or not self.vehicles:
            _LOGGER.error("Reached on_connect, but user and vehicles not loaded")
            return

        for future in self._connected_listeners:
            future.set_result(None)
        self._connected_listeners = []

    def _on_subscribe(
        self,
        client: AsyncioPahoClient,
        _data: None,
        _mid: int,
        _reason_code_list: list[int],
    ) -> None:
        if client is not self.client:
            return

        if self._subscribed_listener is not None:
            listener = self._subscribed_listener
            self._subscribed_listener = None
            listener.set_result(None)

    async def _subscribe_to_topic(self, topic: str) -> None:
        _LOGGER.debug("Subscribing to topic: %s", topic)
        if self._subscribed_listener is not None:
            raise ConcurrentSubscribeError

        future: Future[None] = get_event_loop().create_future()
        self._subscribed_listener = future

        self.client.subscribe(topic)
        await future

    def _emit(self, event: Event) -> None:
        for callback in self._callbacks:
            result = callback(event)
            if result is not None:
                task = create_task(cast(Any, result))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

        self._handle_operation(event)

    def _handle_operation_completed(self, operation: OperationRequest) -> None:
        listeners = self._operation_listeners
        self._operation_listeners = []
        for listener in listeners:
            if listener.operation_name != operation.operation:
                self._operation_listeners.append(listener)
                continue

            if operation.status == OperationStatus.ERROR:
                _LOGGER.error(
                    "Resolving listener for operation '%s' with error '%s'.",
                    operation.operation,
                    operation.error_code,
                )
                listener.future.set_exception(OperationFailedError(operation))
            else:
                if operation.status == OperationStatus.COMPLETED_WARNING:
                    _LOGGER.warning("Operation '%s' completed with warnings.", operation.operation)

                _LOGGER.debug("Resolving listener for operation '%s'.", operation.operation)
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
            return

        _LOGGER.debug(
            "Operation '%s' for trace id '%s' completed.",
            event.operation.operation,
            event.operation.trace_id,
        )
        self._handle_operation_completed(event.operation)

    def _on_message(  # noqa: C901
        self, client: AsyncioPahoClient, _data: None, msg: MQTTMessage
    ) -> None:
        if client is not self.client:
            return

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
        try:
            match event_type:
                case EventType.OPERATION:
                    self._emit(
                        EventOperation(
                            vin=vin,
                            user_id=user_id,
                            timestamp=datetime.now(tz=UTC),
                            operation=OperationRequest.from_json(msg.payload),
                        )
                    )
                case EventType.ACCOUNT_EVENT:
                    self._emit(
                        EventAccountPrivacy(
                            vin=vin,
                            user_id=user_id,
                            timestamp=datetime.now(tz=UTC),
                        )
                    )
                case EventType.SERVICE_EVENT:
                    match topic:
                        case "air-conditioning":
                            self._emit(
                                EventAirConditioning(
                                    vin=vin,
                                    user_id=user_id,
                                    timestamp=datetime.now(tz=UTC),
                                    event=ServiceEvent.from_json(msg.payload),
                                )
                            )
                        case "charging":
                            self._emit(
                                EventCharging(
                                    vin=vin,
                                    user_id=user_id,
                                    timestamp=datetime.now(tz=UTC),
                                    event=ServiceEventCharging.from_json(msg.payload),
                                )
                            )
                        case "vehicle-status/access":
                            self._emit(
                                EventAccess(
                                    vin=vin,
                                    user_id=user_id,
                                    timestamp=datetime.now(tz=UTC),
                                    event=ServiceEvent.from_json(msg.payload),
                                )
                            )
                        case "vehicle-status/lights":
                            self._emit(
                                EventLights(
                                    vin=vin,
                                    user_id=user_id,
                                    timestamp=datetime.now(tz=UTC),
                                    event=ServiceEvent.from_json(msg.payload),
                                )
                            )
        except Exception as exc:  # noqa: BLE001
            _LOGGER.warning("Exception parsing MQTT event: %s", exc)


class OperationFailedError(Exception):
    def __init__(self, operation: OperationRequest) -> None:  # noqa: D107
        op = operation.operation
        error = operation.error_code
        trace = operation.trace_id
        super().__init__(f"Operation {op} with trace {trace} failed: {error}")


class FailedToConnectError(Exception):
    pass


class NotConnectedError(Exception):
    pass


class ConcurrentSubscribeError(Exception):
    pass
