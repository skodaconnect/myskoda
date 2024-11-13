"""Main entry point for the MySkoda library.

This class provides all methods to operate on the API and MQTT broker.
"""

import logging
from asyncio import gather
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from ssl import SSLContext
from traceback import format_exc
from types import SimpleNamespace
from typing import Any

from aiohttp import ClientSession, TraceConfig, TraceRequestEndParams

from myskoda.anonymize import anonymize_url
from myskoda.models.fixtures import (
    Endpoint,
    Fixture,
    FixtureReportGet,
    FixtureReportType,
    FixtureVehicle,
    create_fixture_vehicle,
)

from .auth.authorization import Authorization
from .event import Event
from .models.air_conditioning import AirConditioning
from .models.charging import ChargeMode, Charging
from .models.driving_range import DrivingRange
from .models.health import Health
from .models.info import CapabilityId, Info
from .models.maintenance import Maintenance
from .models.operation_request import OperationName
from .models.position import Positions
from .models.spin import Spin
from .models.status import Status
from .models.trip_statistics import TripStatistics
from .models.user import User
from .mqtt import MySkodaMqttClient
from .rest_api import GetEndpointResult, RestApi
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
    mqtt: MySkodaMqttClient | None = None
    authorization: Authorization
    ssl_context: SSLContext | None = None

    def __init__(  # noqa: D107, PLR0913
        self,
        session: ClientSession,
        ssl_context: SSLContext | None = None,
        mqtt_enabled: bool = True,
        mqtt_broker_host: str | None = None,
        mqtt_broker_port: int | None = None,
        mqtt_enable_ssl: bool | None = None,
    ) -> None:
        self.session = session
        self.authorization = Authorization(session)
        self.rest_api = RestApi(self.session, self.authorization)
        self.ssl_context = ssl_context
        self.mqtt_broker_host = mqtt_broker_host
        self.mqtt_broker_port = mqtt_broker_port
        self.mqtt_enable_ssl = mqtt_enable_ssl
        if mqtt_enabled:
            self.mqtt = self._create_mqtt_client()

    def _create_mqtt_client(self) -> MySkodaMqttClient:
        kwargs = {
            "authorization": self.authorization,
            "hostname": self.mqtt_broker_host,
            "port": self.mqtt_broker_port,
            "enable_ssl": self.mqtt_enable_ssl,
        }
        return MySkodaMqttClient(**{k: v for k, v in kwargs.items() if v is not None})

    async def enable_mqtt(self) -> None:
        """If MQTT was not enabled when initializing MySkoda, enable it manually and connect."""
        if self.mqtt is not None:
            return
        self.mqtt = self._create_mqtt_client()
        user = await self.get_user()
        vehicles = await self.list_vehicle_vins()
        await self.mqtt.connect(user.id, vehicles)

    async def _wait_for_operation(self, operation: OperationName) -> None:
        if self.mqtt is None:
            return
        await self.mqtt.wait_for_operation(operation)

    async def connect(self, email: str, password: str) -> None:
        """Authenticate on the rest api and connect to the MQTT broker."""
        await self.authorization.authorize(email, password)
        _LOGGER.debug("IDK Authorization was successful.")

        if self.mqtt:
            user = await self.get_user()
            vehicles = await self.list_vehicle_vins()
            await self.mqtt.connect(user.id, vehicles)
        _LOGGER.debug("Myskoda ready.")

    def subscribe(self, callback: Callable[[Event], None | Awaitable[None]]) -> None:
        """Listen for events emitted by MySkoda's MQTT broker."""
        if self.mqtt is None:
            raise MqttDisabledError
        self.mqtt.subscribe(callback)

    async def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self.mqtt:
            await self.mqtt.disconnect()

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

    async def set_charge_mode(self, vin: str, mode: ChargeMode) -> None:
        """Set the charge mode."""
        future = self._wait_for_operation(OperationName.UPDATE_CHARGE_MODE)
        await self.rest_api.set_charge_mode(vin, mode=mode)
        await future

    async def honk_flash(self, vin: str) -> None:
        """Honk and flash."""
        future = self._wait_for_operation(OperationName.START_HONK)
        await self.rest_api.honk_flash(vin, (await self.get_positions(vin)).positions)
        await future

    async def flash(self, vin: str) -> None:
        """Flash lights."""
        future = self._wait_for_operation(OperationName.START_FLASH)
        await self.rest_api.flash(vin, (await self.get_positions(vin)).positions)
        await future

    async def wakeup(self, vin: str) -> None:
        """Wake the vehicle up. Can be called maximum three times a day."""
        future = self._wait_for_operation(OperationName.WAKEUP)
        await self.rest_api.wakeup(vin)
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

    async def start_auxiliary_heating(self, vin: str, temperature: float, spin: str) -> None:
        """Start the auxiliary heating with the provided target temperature in °C."""
        # NOTE: 08/11/2024 - no response is published in MQTT (maybe bug in api?) so we don't wait
        future = self._wait_for_operation(OperationName.START_AUXILIARY_HEATING)
        await self.rest_api.start_auxiliary_heating(vin, temperature, spin)
        await future

    async def stop_auxiliary_heating(self, vin: str) -> None:
        """Stop the auxiliary heating."""
        # NOTE: 08/11/2024 - no response is published in MQTT (maybe bug in api?) so we don't wait
        future = self._wait_for_operation(OperationName.STOP_AUXILIARY_HEATING)
        await self.rest_api.stop_auxiliary_heating(vin)
        await future

    async def lock(self, vin: str, spin: str) -> None:
        """Lock the car."""
        future = self._wait_for_operation(OperationName.LOCK)
        await self.rest_api.lock(vin, spin)
        await future

    async def unlock(self, vin: str, spin: str) -> None:
        """Unlock the car."""
        future = self._wait_for_operation(OperationName.UNLOCK)
        await self.rest_api.unlock(vin, spin)
        await future

    async def get_auth_token(self) -> str:
        """Retrieve the main access token for the IDK session."""
        return await self.rest_api.authorization.get_access_token()

    async def verify_spin(self, spin: str, anonymize: bool = False) -> Spin:
        """Verify S-PIN."""
        return (await self.rest_api.verify_spin(spin, anonymize=anonymize)).result

    async def get_info(self, vin: str, anonymize: bool = False) -> Info:
        """Retrieve the basic vehicle information for the specified vehicle."""
        return (await self.rest_api.get_info(vin, anonymize=anonymize)).result

    async def get_charging(self, vin: str, anonymize: bool = False) -> Charging:
        """Retrieve information related to charging for the specified vehicle."""
        return (await self.rest_api.get_charging(vin, anonymize=anonymize)).result

    async def get_status(self, vin: str, anonymize: bool = False) -> Status:
        """Retrieve the current status for the specified vehicle."""
        return (await self.rest_api.get_status(vin, anonymize=anonymize)).result

    async def get_air_conditioning(self, vin: str, anonymize: bool = False) -> AirConditioning:
        """Retrieve the current air conditioning status for the specified vehicle."""
        return (await self.rest_api.get_air_conditioning(vin, anonymize=anonymize)).result

    async def get_positions(self, vin: str, anonymize: bool = False) -> Positions:
        """Retrieve the current position for the specified vehicle."""
        return (await self.rest_api.get_positions(vin, anonymize=anonymize)).result

    async def get_driving_range(self, vin: str, anonymize: bool = False) -> DrivingRange:
        """Retrieve estimated driving range for combustion vehicles."""
        return (await self.rest_api.get_driving_range(vin, anonymize=anonymize)).result

    async def get_trip_statistics(self, vin: str, anonymize: bool = False) -> TripStatistics:
        """Retrieve statistics about past trips."""
        return (await self.rest_api.get_trip_statistics(vin, anonymize=anonymize)).result

    async def get_maintenance(self, vin: str, anonymize: bool = False) -> Maintenance:
        """Retrieve maintenance report."""
        return (await self.rest_api.get_maintenance(vin, anonymize=anonymize)).result

    async def get_health(self, vin: str, anonymize: bool = False) -> Health:
        """Retrieve health information for the specified vehicle."""
        return (await self.rest_api.get_health(vin, anonymize=anonymize)).result

    async def get_user(self, anonymize: bool = False) -> User:
        """Retrieve user information about logged in user."""
        return (await self.rest_api.get_user(anonymize=anonymize)).result

    async def list_vehicle_vins(self) -> list[str]:
        """List all vehicles by their vins."""
        garage = (await self.rest_api.get_garage()).result
        if garage.vehicles is None:
            return []
        return [vehicle.vin for vehicle in garage.vehicles]

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

    async def generate_fixture_report(
        self, vin: str, vehicle: FixtureVehicle, endpoint: Endpoint
    ) -> FixtureReportGet:
        """Generate a fixture report for the specified endpoint and vehicle."""
        try:
            result = await self.get_endpoint(vin, endpoint, anonymize=True)
        except Exception:  # noqa: BLE001
            return FixtureReportGet(
                type=FixtureReportType.GET,
                vehicle_id=vehicle.id,
                success=False,
                endpoint=endpoint,
                error=anonymize_url(format_exc()),
            )
        else:
            return FixtureReportGet(
                type=FixtureReportType.GET,
                vehicle_id=vehicle.id,
                raw=result.raw,
                success=True,
                url=result.url,
                endpoint=endpoint,
                result=result.result.to_dict(),
            )

    async def get_endpoint(
        self, vin: str, endpoint: Endpoint, anonymize: bool = False
    ) -> GetEndpointResult[Any]:
        """Invoke a get endpoint by endpoint enum."""
        result = GetEndpointResult(url="", result=None, raw="")

        if endpoint == Endpoint.INFO:
            result = await self.rest_api.get_info(vin, anonymize=anonymize)
        elif endpoint == Endpoint.STATUS:
            result = await self.rest_api.get_status(vin, anonymize=anonymize)
        elif endpoint == Endpoint.AIR_CONDITIONING:
            result = await self.rest_api.get_air_conditioning(vin, anonymize=anonymize)
        elif endpoint == Endpoint.POSITIONS:
            result = await self.rest_api.get_positions(vin, anonymize=anonymize)
        elif endpoint == Endpoint.HEALTH:
            result = await self.rest_api.get_health(vin, anonymize=anonymize)
        elif endpoint == Endpoint.CHARGING:
            result = await self.rest_api.get_charging(vin, anonymize=anonymize)
        elif endpoint == Endpoint.MAINTENANCE:
            result = await self.rest_api.get_maintenance(vin, anonymize=anonymize)
        elif endpoint == Endpoint.DRIVING_RANGE:
            result = await self.rest_api.get_driving_range(vin, anonymize=anonymize)
        elif endpoint == Endpoint.TRIP_STATISTICS:
            result = await self.rest_api.get_trip_statistics(vin, anonymize=anonymize)
        else:
            raise UnsupportedEndpointError

        return result

    async def generate_get_fixture(
        self, name: str, description: str, vins: list[str], endpoint: Endpoint
    ) -> Fixture:
        """Generate a fixture for a get request."""
        vehicles = [
            (vin, create_fixture_vehicle(i, await self.get_info(vin))) for i, vin in enumerate(vins)
        ]

        endpoints = []
        if endpoint != Endpoint.ALL:
            endpoints = [endpoint]
        else:
            endpoints = filter(lambda ep: ep != Endpoint.ALL, Endpoint)

        reports = [
            await self.generate_fixture_report(vin, vehicle, endpoint)
            for (vin, vehicle) in vehicles
            for endpoint in endpoints
        ]

        return Fixture(
            name=name,
            description=description,
            generation_time=datetime.now(tz=UTC),
            vehicles=[vehicle for (_, vehicle) in vehicles],
            reports=reports,
        )


class MqttDisabledError(Exception):
    """MQTT was not enabled."""


class UnsupportedEndpointError(Exception):
    """Endpoint not implemented."""
