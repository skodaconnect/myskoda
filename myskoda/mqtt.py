"""MQTT client module for the MySkoda server."""

import logging
import ssl
from typing import Any

from paho.mqtt.client import Client, MQTTMessage

from .const import MQTT_HOST, MQTT_PORT
from .models.user import User
from .rest_api import RestApi

_LOGGER = logging.getLogger(__name__)


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
        self.client.tls_insecure_set(value=True)
        self.client.username_pw_set(
            self.user.id, await self.api.idk_session.get_access_token(self.api.session)
        )
        self.client.connect(MQTT_HOST, MQTT_PORT, 60)

    def loop_forever(self) -> None:
        """Make the MQTT client process new messages until the current process is cancelled."""
        self.client.loop_forever()

    def _on_connect(self, client: Client, _userdata: Any, _flags: Any, reason: int) -> None:  # noqa: ANN401
        print(f"MQTT Connected. {reason}")
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

    def _on_message(self, _client: Client, _userdata: Any, msg: MQTTMessage) -> None:  # noqa: ANN401
        print(f"{msg.topic}: {msg.payload}")
