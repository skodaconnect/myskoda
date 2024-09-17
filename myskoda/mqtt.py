"""MQTT client module for the MySkoda server."""

import json
import logging
import re
import ssl
from collections.abc import Callable
from typing import cast

from paho.mqtt.client import Client, MQTTMessage

from .const import MQTT_BROKER_HOST, MQTT_BROKER_PORT
from .event import (
    Event,
    EventAccess,
    EventAccountPrivacy,
    EventAirConditioning,
    EventApplyBackup,
    EventCharging,
    EventHonkAndFlash,
    EventLights,
    EventLockVehicle,
    EventSetTargetTemperature,
    EventStartStopAirConditioning,
    EventStartStopCharging,
    EventStartStopWindowHeating,
    EventUpdateBatterySupport,
    EventWakeup,
)
from .models.user import User
from .rest_api import RestApi

_LOGGER = logging.getLogger(__name__)
TOPIC_RE = re.compile("^(.*?)/(.*?)/(.*?)$")


class MQTT:
    api: RestApi
    user: User
    vehicles: list[str]
    _callbacks: list[Callable[[Event], None]]

    def __init__(self, api: RestApi) -> None:  # noqa: D107
        self.api = api
        self.callbacks = []

    def subscribe(self, callback: Callable[[Event], None]) -> None:
        """Listen for events emitted by MySkoda's MQTT broker."""
        self.callbacks.append(callback)

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

    def _on_connect(self, client: Client, _data: None, _flags: dict, _reason: int) -> None:
        _LOGGER.info("MQTT Connected.")
        user_id = self.user.id

        for vin in self.vehicles:
            client.subscribe(f"{user_id}/{vin}/account-event/privacy")
            client.subscribe(f"{user_id}/{vin}/operation-request/charging/update-battery-support")
            client.subscribe(f"{user_id}/{vin}/operation-request/vehicle-access/lock-vehicle")
            client.subscribe(f"{user_id}/{vin}/operation-request/vehicle-wakeup/wakeup")
            client.subscribe(f"{user_id}/{vin}/service-event/vehicle-status/access")
            client.subscribe(f"{user_id}/{vin}/service-event/vehicle-status/lights")
            client.subscribe(
                f"{user_id}/{vin}/operation-request/air-conditioning/set-target-temperature"
            )
            client.subscribe(
                f"{user_id}/{vin}/operation-request/air-conditioning/start-stop-air-conditioning"
            )
            client.subscribe(
                f"{user_id}/{vin}/operation-request/air-conditioning/start-stop-window-heating"
            )
            client.subscribe(f"{user_id}/{vin}/operation-request/charging/start-stop-charging")
            client.subscribe(
                f"{user_id}/{vin}/operation-request/vehicle-services-backup/apply-backup"
            )
            client.subscribe(f"{user_id}/{vin}/service-event/air-conditioning")
            client.subscribe(f"{user_id}/{vin}/service-event/charging")
            client.subscribe(f"{user_id}/{vin}/operation-request/vehicle-access/honk-and-flash")
            client.subscribe(
                f"{user_id}/{vin}/operation-request/vehicle-services-backup/apply-backup"
            )

    def _emit(self, event: Event) -> None:
        for callback in self.callbacks:
            callback(event)

    def _on_message(self, _client: Client, _data: None, msg: MQTTMessage) -> None:  # noqa: C901, PLR0912
        # Extract the topic, user id and vin from the topic's name.
        # Internally, the topic will always look like this:
        # `/{user_id}/{vin}/path/to/topic`
        topic_match = TOPIC_RE.match(msg.topic)
        if not topic_match:
            _LOGGER.warning("Unexpected MQTT topic encountered: %s", topic_match)
            return

        [user_id, vin, topic] = topic_match.groups()

        # Cast the data from binary string, ignoring empty messages.
        data = cast(str, msg.payload)
        if len(data) == 0:
            return

        _LOGGER.debug("Message received for %s (%s): %s", vin, topic, data)

        # Messages will contain payload as JSON.
        data = json.loads(msg.payload)

        match topic:
            case "account-event/privacy":
                self._emit(EventAccountPrivacy(vin, user_id, data))
            case "operation-request/charging/update-battery-support":
                self._emit(EventUpdateBatterySupport(vin, user_id, data))
            case "operation-request/vehicle-access/lock-vehicle":
                self._emit(EventLockVehicle(vin, user_id, data))
            case "operation-request/vehicle-wakeup/wakeup":
                self._emit(EventWakeup(vin, user_id, data))
            case "operation-request/air-conditioning/set-target-temperature":
                self._emit(EventSetTargetTemperature(vin, user_id, data))
            case "operation-request/air-conditioning/start-stop-air-conditioning":
                self._emit(EventStartStopAirConditioning(vin, user_id, data))
            case "operation-request/air-conditioning/start-stop-window-heating":
                self._emit(EventStartStopWindowHeating(vin, user_id, data))
            case "operation-request/charging/start-stop-charging":
                self._emit(EventStartStopCharging(vin, user_id, data))
            case "operation-request/vehicle-services-backup/apply-backup":
                self._emit(EventApplyBackup(vin, user_id, data))
            case "operation-request/vehicle-access/honk-and-flash":
                self._emit(EventHonkAndFlash(vin, user_id, data))
            case "service-event/air-conditioning":
                self._emit(EventAirConditioning(vin, user_id, data))
            case "service-event/charging":
                self._emit(EventCharging(vin, user_id, data))
            case "service-event/vehicle-status/access":
                self._emit(EventAccess(vin, user_id, data))
            case "service-event/vehicle-status/lights":
                self._emit(EventLights(vin, user_id, data))
