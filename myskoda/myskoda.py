"""Main entry point for the MySkoda library.

This class provides all methods to operate on the API and MQTT broker.
"""

import logging
from collections.abc import Callable

from aiohttp import ClientSession

from .event import Event
from .models.mqtt import OperationName
from .mqtt import Mqtt
from .rest_api import RestApi

_LOGGER = logging.getLogger(__name__)


class MySkoda:
    session: ClientSession
    rest_api: RestApi
    mqtt: Mqtt

    def __init__(self, session: ClientSession) -> None:  # noqa: D107
        self.session = session
        self.rest_api = RestApi(self.session)
        self.mqtt = Mqtt(self.rest_api)

    async def connect(self, email: str, password: str) -> None:
        """Authenticate on the rest api and connect to the MQTT broker."""
        await self.rest_api.authenticate(email, password)
        await self.mqtt.connect()
        _LOGGER.debug("Myskoda ready.")

    def subscribe(self, callback: Callable[[Event], None]) -> None:
        """Listen for events emitted by MySkoda's MQTT broker."""
        self.mqtt.subscribe(callback)

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.mqtt.disconnect()

    async def stop_charging(self, vin: str) -> None:
        """Stop the car from charging."""
        future = self.mqtt.wait_for_operation(OperationName.STOP_CHARGING)
        await self.rest_api.stop_charging(vin)
        await future

    async def start_charging(self, vin: str) -> None:
        """Start charging the car."""
        future = self.mqtt.wait_for_operation(OperationName.START_CHARGING)
        await self.rest_api.stop_charging(vin)
        await future

    async def honk_flash(self, vin: str, honk: bool = False) -> None:  # noqa: FBT002
        """Honk and/or flash."""
        future = self.mqtt.wait_for_operation(OperationName.START_HONK)
        await self.rest_api.honk_flash(vin, honk)
        await future

    async def wakeup(self, vin: str) -> None:
        """Wake the vehicle up. Can be called maximum three times a day."""
        future = self.mqtt.wait_for_operation(OperationName.WAKEUP)
        await self.rest_api.honk_flash(vin)
        await future

    async def set_reduced_current_limit(self, vin: str, reduced: bool) -> None:
        """Enable reducing the current limit by which the car is charged."""
        future = self.mqtt.wait_for_operation(OperationName.UPDATE_CHARGING_CURRENT)
        await self.rest_api.set_reduced_current_limit(vin, reduced=reduced)
        await future

    async def set_battery_care_mode(self, vin: str, enabled: bool) -> None:
        """Enable or disable the battery care mode."""
        future = self.mqtt.wait_for_operation(OperationName.UPDATE_CARE_MODE)
        await self.rest_api.set_battery_care_mode(vin, enabled)
        await future

    async def set_charge_limit(self, vin: str, limit: int) -> None:
        """Set the maximum charge limit in percent."""
        future = self.mqtt.wait_for_operation(OperationName.UPDATE_CHARGE_LIMIT)
        await self.rest_api.set_charge_limit(vin, limit)
        await future

    async def stop_window_heating(self, vin: str) -> None:
        """Stop heating both the front and rear window."""
        future = self.mqtt.wait_for_operation(OperationName.STOP_WINDOW_HEATING)
        await self.rest_api.stop_window_heating(vin)
        await future

    async def start_window_heating(self, vin: str) -> None:
        """Start heating both the front and rear window."""
        future = self.mqtt.wait_for_operation(OperationName.START_WINDOW_HEATING)
        await self.rest_api.start_window_heating(vin)
        await future

    async def set_target_temperature(self, vin: str, temperature: float) -> None:
        """Set the air conditioning's target temperature in °C."""
        future = self.mqtt.wait_for_operation(OperationName.UPDATE_TARGET_TEMPERATURE)
        await self.rest_api.set_target_temperature(vin, temperature)
        await future

    async def start_air_conditioning(self, vin: str, temperature: float) -> None:
        """Start the air conditioning with the provided target temperature in °C."""
        future = self.mqtt.wait_for_operation(OperationName.START_AIR_CONDITIONING)
        await self.rest_api.start_air_conditioning(vin, temperature)
        await future

    async def stop_air_conditioning(self, vin: str) -> None:
        """Stop the air conditioning."""
        future = self.mqtt.wait_for_operation(OperationName.STOP_AIR_CONDITIONING)
        await self.rest_api.stop_air_conditioning(vin)
        await future

    def get_auth_token(self) -> str:
        """Retrieve the main access token for the IDK session."""
        return self.rest_api.idk_session.access_token
