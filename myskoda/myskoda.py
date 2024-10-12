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

from aiohttp import ClientSession, TraceConfig, TraceRequestEndParams

from myskoda.anonymize import VIN
from myskoda.models.fixtures import (
    Endpoint,
    Fixture,
    FixtureReportGet,
    FixtureReportType,
    FixtureVehicle,
    GetEndpointResult,
    create_fixture_vehicle,
)
from myskoda.models.garage import Garage

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
            self.mqtt = Mqtt(self.authorization, ssl_context=self.ssl_context)

    async def enable_mqtt(self) -> None:
        """If MQTT was not enabled when initializing MySkoda, enable it manually and connect."""
        if self.mqtt is not None:
            return
        self.mqtt = Mqtt(self.authorization, ssl_context=self.ssl_context)
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
        await self.rest_api.honk_flash(vin, (await self.get_positions(vin)).positions, honk)
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

    async def get_auth_token(self) -> str:
        """Retrieve the main access token for the IDK session."""
        return await self.rest_api.authorization.get_access_token()

    async def get_info(self, vin: str, anonymize: bool = False, raw: str | None = None) -> Info:
        """Retrieve the basic vehicle information for the specified vehicle."""
        if raw is None:
            raw = await self.rest_api.get_info_raw(vin, anonymize)
        return self._deserialize(raw, Info.from_json)

    async def get_charging(
        self, vin: str, anonymize: bool = False, raw: str | None = None
    ) -> Charging:
        """Retrieve information related to charging for the specified vehicle."""
        if raw is None:
            raw = await self.rest_api.get_charging_raw(vin, anonymize)
        return self._deserialize(raw, Charging.from_json)

    async def get_status(self, vin: str, anonymize: bool = False, raw: str | None = None) -> Status:
        """Retrieve the current status for the specified vehicle."""
        if raw is None:
            raw = await self.rest_api.get_status_raw(vin, anonymize)
        return self._deserialize(raw, Status.from_json)

    async def get_air_conditioning(
        self, vin: str, anonymize: bool = False, raw: str | None = None
    ) -> AirConditioning:
        """Retrieve the current air conditioning status for the specified vehicle."""
        if raw is None:
            raw = await self.rest_api.get_air_conditioning_raw(vin, anonymize)
        return self._deserialize(raw, AirConditioning.from_json)

    async def get_positions(
        self, vin: str, anonymize: bool = False, raw: str | None = None
    ) -> Positions:
        """Retrieve the current position for the specified vehicle."""
        if raw is None:
            raw = await self.rest_api.get_positions_raw(vin, anonymize)
        return self._deserialize(raw, Positions.from_json)

    async def get_driving_range(
        self, vin: str, anonymize: bool = False, raw: str | None = None
    ) -> DrivingRange:
        """Retrieve estimated driving range for combustion vehicles."""
        if raw is None:
            raw = await self.rest_api.get_driving_range_raw(vin, anonymize)
        return self._deserialize(raw, DrivingRange.from_json)

    async def get_trip_statistics(
        self, vin: str, anonymize: bool = False, raw: str | None = None
    ) -> TripStatistics:
        """Retrieve statistics about past trips."""
        if raw is None:
            raw = await self.rest_api.get_trip_statistics_raw(vin, anonymize)
        return self._deserialize(raw, TripStatistics.from_json)

    async def get_maintenance(
        self, vin: str, anonymize: bool = False, raw: str | None = None
    ) -> Maintenance:
        """Retrieve maintenance report."""
        if raw is None:
            raw = await self.rest_api.get_maintenance_raw(vin, anonymize)
        return self._deserialize(raw, Maintenance.from_json)

    async def get_health(self, vin: str, anonymize: bool = False, raw: str | None = None) -> Health:
        """Retrieve health information for the specified vehicle."""
        if raw is None:
            raw = await self.rest_api.get_health_raw(vin, anonymize)
        return self._deserialize(raw, Health.from_json)

    async def get_user(self, anonymize: bool = False, raw: str | None = None) -> User:
        """Retrieve user information about logged in user."""
        if raw is None:
            raw = await self.rest_api.get_user_raw(anonymize)
        return self._deserialize(raw, User.from_json)

    async def get_garage(self, anonymize: bool = False, raw: str | None = None) -> Garage:
        """Fetch the garage (list of vehicles with limited info)."""
        if raw is None:
            raw = await self.rest_api.get_garage_raw(anonymize)
        return self._deserialize(raw, Garage.from_json)

    async def list_vehicle_vins(self) -> list[str]:
        """List all vehicles by their vins."""
        garage = await self.get_garage()
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

    def _deserialize[T](self, text: str, deserialize: Callable[[str], T]) -> T:
        try:
            data = deserialize(text)
        except Exception:
            _LOGGER.exception("Failed to deserialize data: %s", text)
            raise
        else:
            return data

    async def generate_fixture_report(
        self, vin: str, vehicle: FixtureVehicle, endpoint: Endpoint
    ) -> FixtureReportGet:
        """Generate a fixture report for the specified endpoint and vehicle."""
        try:
            result = await self._get_endpoint_result(vin, endpoint)
        except Exception:  # noqa: BLE001
            return FixtureReportGet(
                type=FixtureReportType.GET,
                vehicle_id=vehicle.id,
                success=False,
                endpoint=endpoint,
                error=format_exc(),
            )
        else:
            return FixtureReportGet(
                type=FixtureReportType.GET,
                vehicle_id=vehicle.id,
                raw=result.raw,
                success=True,
                url=result.url,
                endpoint=endpoint,
                result=result.result,
            )

    async def _get_endpoint_result(self, vin: str, endpoint: Endpoint) -> GetEndpointResult:
        url = ""
        raw = ""
        result = {}

        if endpoint == Endpoint.INFO:
            url = self.rest_api.get_info_url(vin).replace(vin, VIN)
            raw = await self.rest_api.get_info_raw(vin, anonymize=True)
            result = (await self.get_info(vin, anonymize=True, raw=raw)).to_dict()
        elif endpoint == Endpoint.STATUS:
            url = self.rest_api.get_status_url(vin).replace(vin, VIN)
            raw = await self.rest_api.get_status_raw(vin, anonymize=True)
            result = (await self.get_status(vin, anonymize=True, raw=raw)).to_dict()
        elif endpoint == Endpoint.AIR_CONDITIONING:
            url = self.rest_api.get_air_conditioning_url(vin).replace(vin, VIN)
            raw = await self.rest_api.get_air_conditioning_raw(vin, anonymize=True)
            result = (await self.get_air_conditioning(vin, anonymize=True, raw=raw)).to_dict()
        elif endpoint == Endpoint.POSITIONS:
            url = self.rest_api.get_positions_url(vin).replace(vin, VIN)
            raw = await self.rest_api.get_positions_raw(vin, anonymize=True)
            result = (await self.get_positions(vin, anonymize=True, raw=raw)).to_dict()
        elif endpoint == Endpoint.HEALTH:
            url = self.rest_api.get_health_url(vin).replace(vin, VIN)
            raw = await self.rest_api.get_health_raw(vin, anonymize=True)
            result = (await self.get_health(vin, anonymize=True, raw=raw)).to_dict()
        elif endpoint == Endpoint.CHARGING:
            url = self.rest_api.get_charging_url(vin).replace(vin, VIN)
            raw = await self.rest_api.get_charging_raw(vin, anonymize=True)
            result = (await self.get_charging(vin, anonymize=True, raw=raw)).to_dict()
        elif endpoint == Endpoint.MAINTENANCE:
            url = self.rest_api.get_maintenance_url(vin).replace(vin, VIN)
            raw = await self.rest_api.get_maintenance_raw(vin, anonymize=True)
            result = (await self.get_maintenance(vin, anonymize=True, raw=raw)).to_dict()
        elif endpoint == Endpoint.DRIVING_RANGE:
            url = self.rest_api.get_driving_range_url(vin).replace(vin, VIN)
            raw = await self.rest_api.get_driving_range_raw(vin, anonymize=True)
            result = (await self.get_driving_range(vin, anonymize=True, raw=raw)).to_dict()
        elif endpoint == Endpoint.TRIP_STATISTICS:
            url = self.rest_api.get_trip_statistics_url(vin).replace(vin, VIN)
            raw = await self.rest_api.get_trip_statistics_raw(vin, anonymize=True)
            result = (await self.get_trip_statistics(vin, anonymize=True, raw=raw)).to_dict()
        else:
            raise UnsupportedEndpointError

        return GetEndpointResult(url=url, raw=raw, result=result)

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
