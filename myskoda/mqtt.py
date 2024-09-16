"""MQTT client module for the MySkoda server."""

import json
import logging
import re
import ssl
from enum import StrEnum
from typing import Literal, cast

from paho.mqtt.client import Client, MQTTMessage

from myskoda.models.mqtt import OperationRequest, ServiceEvent, ServiceEventCharging

from .const import MQTT_HOST, MQTT_PORT
from .models.user import User
from .rest_api import RestApi

_LOGGER = logging.getLogger(__name__)
TOPIC_RE = re.compile("^(.*?)/(.*?)/(.*?)$")


class Topic(StrEnum):
    UPDATE_BATTERY_SUPPORT = "UPDATE_BATTERY_SUPPORT"
    LOCK_VEHICLE = "LOCK_VEHICLE"
    WAKEUP = "WAKEUP"
    SET_TARGET_TEMPERATURE = "SET_TARGET_TEMPERATURE"
    START_STOP_AIR_CONDITIONING = "START_STOP_AIR_CONDITIONING"
    START_STOP_WINDOW_HEATING = "START_STOP_WINDOW_HEATING"
    START_STOP_CHARGING = "START_STOP_CHARGING"
    APPLY_BACKUP = "APPLY_BACKUP"
    HONK_AND_FLASH = "HONK_AND_FLASH"
    AIR_CONDITIONING = "AIR_CONDITIONING"
    CHARGING = "CHARGING"
    ACCESS = "ACCESS"
    LIGHTS = "LIGHTS"


class EventUpdateBatterySupport:
    topic: Literal[Topic.UPDATE_BATTERY_SUPPORT]
    payload: OperationRequest

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.UPDATE_BATTERY_SUPPORT
        self.payload = OperationRequest(**payload)


class EventLockVehicle:
    topic: Literal[Topic.LOCK_VEHICLE]
    payload: OperationRequest

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.LOCK_VEHICLE
        self.payload = OperationRequest(**payload)


class EventWakeup:
    topic: Literal[Topic.WAKEUP]
    payload: OperationRequest

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.WAKEUP
        self.payload = OperationRequest(**payload)


class EventSetTargetTemperature:
    topic: Literal[Topic.SET_TARGET_TEMPERATURE]
    payload: OperationRequest

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.SET_TARGET_TEMPERATURE
        self.payload = OperationRequest(**payload)


class EventStartStopAirConditioning:
    topic: Literal[Topic.START_STOP_AIR_CONDITIONING]
    payload: OperationRequest

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.START_STOP_AIR_CONDITIONING
        self.payload = OperationRequest(**payload)


class EventStartStopWindowHeating:
    topic: Literal[Topic.START_STOP_WINDOW_HEATING]
    payload: OperationRequest

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.START_STOP_WINDOW_HEATING
        self.payload = OperationRequest(**payload)


class EventStartStopCharging:
    topic: Literal[Topic.START_STOP_CHARGING]
    payload: OperationRequest

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.START_STOP_CHARGING
        self.payload = OperationRequest(**payload)


class EventHonkAndFlash:
    topic: Literal[Topic.HONK_AND_FLASH]
    payload: OperationRequest

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.HONK_AND_FLASH
        self.payload = OperationRequest(**payload)


class EventApplyBackup:
    topic: Literal[Topic.APPLY_BACKUP]
    payload: OperationRequest

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.APPLY_BACKUP
        self.payload = OperationRequest(**payload)


class EventAirConditioning:
    topic: Literal[Topic.AIR_CONDITIONING]
    payload: ServiceEvent

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.AIR_CONDITIONING
        self.payload = ServiceEvent(**payload)


class EventCharging:
    topic: Literal[Topic.CHARGING]
    payload: ServiceEventCharging

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.CHARGING
        self.payload = ServiceEventCharging(**payload)


class EventAccess:
    topic: Literal[Topic.ACCESS]
    payload: ServiceEvent

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.ACCESS
        self.payload = ServiceEvent(**payload)


class EventLights:
    topic: Literal[Topic.LIGHTS]
    payload: ServiceEvent

    def __init__(self, payload: dict) -> None:  # noqa: D107
        self.topic = Topic.LIGHTS
        self.payload = ServiceEvent(**payload)


Event = (
    EventUpdateBatterySupport
    | EventLockVehicle
    | EventWakeup
    | EventSetTargetTemperature
    | EventStartStopAirConditioning
    | EventStartStopWindowHeating
    | EventStartStopCharging
    | EventApplyBackup
    | EventHonkAndFlash
    | EventApplyBackup
    | EventAirConditioning
    | EventCharging
    | EventAccess
    | EventLights
)


class MQTT:
    api: RestApi
    user: User
    vehicles: list[str]

    def __init__(self, api: RestApi) -> None:  # noqa: D107
        self.api = api

    async def connect(self) -> None:
        """Connect to the MQTT broker and listen for messages."""
        _LOGGER.info(f"Connecting to MQTT on {MQTT_HOST}:{MQTT_PORT}...")
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
        self.client.connect(MQTT_HOST, MQTT_PORT, 60)

    def loop_forever(self) -> None:
        """Make the MQTT client process new messages until the current process is cancelled."""
        self.client.loop_forever()

    def _on_connect(self, client: Client, _userdata: None, _flags: dict, _reason: int) -> None:
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
        print(event)

    def _on_message(self, _client: Client, _userdata: None, msg: MQTTMessage) -> None:  # noqa: C901, PLR0912
        topic_match = TOPIC_RE.match(msg.topic)

        if not topic_match:
            _LOGGER.warning("Unexpected MQTT topic encountered: %s", topic_match)
            return

        [_user_id, vin, topic] = topic_match.groups()
        data = cast(str, msg.payload)

        if len(data) == 0:
            return

        _LOGGER.debug("Message received for %s (%s): %s", vin, topic, data)

        data = json.loads(msg.payload)

        if topic == "account-event/privacy":
            pass
        elif topic == "operation-request/charging/update-battery-support":
            self._emit(EventUpdateBatterySupport(data))
        elif topic == "operation-request/vehicle-access/lock-vehicle":
            self._emit(EventLockVehicle(data))
        elif topic == "operation-request/vehicle-wakeup/wakeup":
            self._emit(EventWakeup(data))
        elif topic == "operation-request/air-conditioning/set-target-temperature":
            self._emit(EventSetTargetTemperature(data))
        elif topic == "operation-request/air-conditioning/start-stop-air-conditioning":
            self._emit(EventStartStopAirConditioning(data))
        elif topic == "operation-request/air-conditioning/start-stop-window-heating":
            self._emit(EventStartStopWindowHeating(data))
        elif topic == "operation-request/charging/start-stop-charging":
            self._emit(EventStartStopCharging(data))
        elif topic == "operation-request/vehicle-services-backup/apply-backup":
            self._emit(EventApplyBackup(data))
        elif topic == "operation-request/vehicle-access/honk-and-flash":
            self._emit(EventHonkAndFlash(data))
        elif topic == "service-event/air-conditioning":
            self._emit(EventAirConditioning(data))
        elif topic == "service-event/charging":
            self._emit(EventCharging(data))
        elif topic == "service-event/vehicle-status/access":
            self._emit(EventAccess(data))
        elif topic == "service-event/vehicle-status/lights":
            self._emit(EventLights(data))
