"""Main entry point for the MySkoda library.

This class provides all methods to operate on the API and MQTT broker.
"""

import logging
from asyncio import gather
from collections.abc import Awaitable, Callable
from ssl import SSLContext
from types import SimpleNamespace

from aiohttp import ClientSession, TraceConfig, TraceRequestEndParams

from .auth.authorization import Authorization
from .event import Event
from .models.air_conditioning import AirConditioning
from .models.charging import Charging
from .models.driving_range import DrivingRange
from .models.health import Health
from .models.info import CapabilityId, Info
from .models.maintenance import Maintenance
from .models.operation_request import OperationName
from .models.position import Positions
from .models.status import Status
from .models.trip_statistics import TripStatistics
from .models.user import User
from .mqtt import Mqtt
from .rest_api import RestApi
from .vehicle import Vehicle

_LOGGER = logging.getLogger(__name__)


async def trace_response(
    _session: ClientSession,
    _trace_config_ctx: SimpleNamespace,
    params: TraceRequestEndParams,
) -> None:
    """Log response details. Used in aiohttp.TraceConfig."""
    resp_text = await params.response.text()
    _LOGGER.debug(
        "Trace: %s %s - response: %s (%s bytes) %s",
        params.method,
        str(params.url)[:60],
        params.response.status,
        params.response.content_length,
        resp_text[:5000],
    )


TRACE_CONFIG = TraceConfig()
TRACE_CONFIG.on_request_end.append(trace_response)


class MySkoda:
    session: ClientSession
    rest_api: RestApi
    mqtt: Mqtt | None = None
    authorization: Authorization
    ssl_context: SSLContext | None = None

    def __init__(  # noqa: D107
        self,
        session: ClientSession,
        ssl_context: SSLContext | None = None,
        mqtt_enabled: bool = True,
    ) -> None:
        self.session = session
        self.authorization = Authorization(session)
        self.rest_api = RestApi(self.session, self.authorization)
        self.ssl_context = ssl_context
        if mqtt_enabled:
            self.mqtt = Mqtt(self.authorization, self.rest_api, ssl_context=self.ssl_context)

    async def enable_mqtt(self) -> None:
        """If MQTT was not enabled when initializing MySkoda, enable it manually and connect."""
        if self.mqtt is not None:
            return
        self.mqtt = Mqtt(self.authorization, self.rest_api, ssl_context=self.ssl_context)
        await self.mqtt.connect()

    async def _wait_for_operation(self, operation: OperationName) -> None:
        if self.mqtt is None:
            return
        await self.mqtt.wait_for_operation(operation)

    async def connect(self, email: str, password: str) -> None:
        """Authenticate on the rest api and connect to the MQTT broker."""
        await self.authorization.authorize(email, password)
        _LOGGER.debug("IDK Authorization was successful.")

        if self.mqtt:
            await self.mqtt.connect()
        _LOGGER.debug("Myskoda ready.")

    def subscribe(self, callback: Callable[[Event], None | Awaitable[None]]) -> None:
        """Listen for events emitted by MySkoda's MQTT broker."""
        if self.mqtt is None:
            raise MqttDisabledError
        self.mqtt.subscribe(callback)

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self.mqtt:
            self.mqtt.disconnect()

    async def stop_charging(self, vin: str) -> None:
        """Stop the car from charging."""
        future = self._wait_for_operation(OperationName.STOP_CHARGING)
        await self.rest_api.stop_charging(vin)
        await future

    async def start_charging(self, vin: str) -> None:
        """Start charging the car."""
        future = self._wait_for_operation(OperationName.START_CHARGING)
        await self.rest_api.start_charging(vin)
        await future

    async def honk_flash(self, vin: str, honk: bool = False) -> None:
        """Honk and/or flash."""
        future = self._wait_for_operation(OperationName.START_HONK)
        await self.rest_api.honk_flash(vin, honk)
        await future

    async def wakeup(self, vin: str) -> None:
        """Wake the vehicle up. Can be called maximum three times a day."""
        future = self._wait_for_operation(OperationName.WAKEUP)
        await self.rest_api.honk_flash(vin)
        await future

    async def set_reduced_current_limit(self, vin: str, reduced: bool) -> None:
        """Enable reducing the current limit by which the car is charged."""
        future = self._wait_for_operation(OperationName.UPDATE_CHARGING_CURRENT)
        await self.rest_api.set_reduced_current_limit(vin, reduced=reduced)
        await future

    async def set_battery_care_mode(self, vin: str, enabled: bool) -> None:
        """Enable or disable the battery care mode."""
        future = self._wait_for_operation(OperationName.UPDATE_CARE_MODE)
        await self.rest_api.set_battery_care_mode(vin, enabled)
        await future

    async def set_charge_limit(self, vin: str, limit: int) -> None:
        """Set the maximum charge limit in percent."""
        future = self._wait_for_operation(OperationName.UPDATE_CHARGE_LIMIT)
        await self.rest_api.set_charge_limit(vin, limit)
        await future

    async def stop_window_heating(self, vin: str) -> None:
        """Stop heating both the front and rear window."""
        future = self._wait_for_operation(OperationName.STOP_WINDOW_HEATING)
        await self.rest_api.stop_window_heating(vin)
        await future

    async def start_window_heating(self, vin: str) -> None:
        """Start heating both the front and rear window."""
        future = self._wait_for_operation(OperationName.START_WINDOW_HEATING)
        await self.rest_api.start_window_heating(vin)
        await future

    async def set_target_temperature(self, vin: str, temperature: float) -> None:
        """Set the air conditioning's target temperature in °C."""
        future = self._wait_for_operation(OperationName.SET_AIR_CONDITIONING_TARGET_TEMPERATURE)
        await self.rest_api.set_target_temperature(vin, temperature)
        await future

    async def start_air_conditioning(self, vin: str, temperature: float) -> None:
        """Start the air conditioning with the provided target temperature in °C."""
        future = self._wait_for_operation(OperationName.START_AIR_CONDITIONING)
        await self.rest_api.start_air_conditioning(vin, temperature)
        await future

    async def stop_air_conditioning(self, vin: str) -> None:
        """Stop the air conditioning."""
        future = self._wait_for_operation(OperationName.STOP_AIR_CONDITIONING)
        await self.rest_api.stop_air_conditioning(vin)
        await future

    async def get_auth_token(self) -> str:
        """Retrieve the main access token for the IDK session."""
        return await self.rest_api.authorization.get_access_token()

    async def get_info(self, vin: str) -> Info:
        """Retrieve the basic vehicle information for the specified vehicle."""
        return await self.rest_api.get_info(vin)

    async def get_charging(self, vin: str) -> Charging:
        """Retrieve information related to charging for the specified vehicle."""
        return await self.rest_api.get_charging(vin)

    async def get_status(self, vin: str) -> Status:
        """Retrieve the current status for the specified vehicle."""
        return await self.rest_api.get_status(vin)

    async def get_air_conditioning(self, vin: str) -> AirConditioning:
        """Retrieve the current air conditioning status for the specified vehicle."""
        return await self.rest_api.get_air_conditioning(vin)

    async def get_positions(self, vin: str) -> Positions:
        """Retrieve the current position for the specified vehicle."""
        return await self.rest_api.get_positions(vin)

    async def get_driving_range(self, vin: str) -> DrivingRange:
        """Retrieve estimated driving range for combustion vehicles."""
        return await self.rest_api.get_driving_range(vin)

    async def get_trip_statistics(self, vin: str) -> TripStatistics:
        """Retrieve statistics about past trips."""
        return await self.rest_api.get_trip_statistics(vin)

    async def get_maintenance(self, vin: str) -> Maintenance:
        """Retrieve maintenance report."""
        return await self.rest_api.get_maintenance(vin)

    async def get_health(self, vin: str) -> Health:
        """Retrieve health information for the specified vehicle."""
        return await self.rest_api.get_health(vin)

    async def get_user(self) -> User:
        """Retrieve user information about logged in user."""
        return await self.rest_api.get_user()

    async def list_vehicle_vins(self) -> list[str]:
        """List all vehicles by their vins."""
        return await self.rest_api.list_vehicles()

    async def get_vehicle(self, vin: str) -> Vehicle:
        """Load a full vehicle based on its capabilities."""
        info = await self.get_info(vin)
        maintenance = await self.get_maintenance(vin)

        vehicle = Vehicle(info, maintenance)

        if info.is_capability_available(CapabilityId.STATE):
            vehicle.status = await self.get_status(vin)
            vehicle.driving_range = await self.get_driving_range(vin)

        if info.is_capability_available(CapabilityId.AIR_CONDITIONING):
            vehicle.air_conditioning = await self.get_air_conditioning(vin)

        if info.is_capability_available(CapabilityId.PARKING_POSITION):
            vehicle.positions = await self.get_positions(vin)

        if info.is_capability_available(CapabilityId.TRIP_STATISTICS):
            vehicle.trip_statistics = await self.get_trip_statistics(vin)

        if info.is_capability_available(CapabilityId.CHARGING):
            vehicle.charging = await self.get_charging(vin)

        if info.is_capability_available(CapabilityId.VEHICLE_HEALTH_INSPECTION):
            vehicle.health = await self.get_health(vin)

        return vehicle

    async def get_all_vehicles(self) -> list[Vehicle]:
        """Load all vehicles based on their capabilities."""
        vins = await self.list_vehicle_vins()
        return await gather(*(self.get_vehicle(vin) for vin in vins))


class MqttDisabledError(Exception):
    """MQTT was not enabled."""
