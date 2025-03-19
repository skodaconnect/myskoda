"""Main entry point for the MySkoda library.

This class provides all methods to operate on the API and MQTT broker.
"""

import logging
from asyncio import gather, timeout
from collections.abc import Awaitable, Callable
from copy import deepcopy
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

from .__version__ import __version__ as version
from .auth.authorization import Authorization
from .const import BASE_URL_SKODA, CLIENT_ID, MQTT_OPERATION_TIMEOUT, REDIRECT_URI
from .event import Event
from .models.air_conditioning import (
    AirConditioning,
    AirConditioningAtUnlock,
    AirConditioningTimer,
    AirConditioningWithoutExternalPower,
    SeatHeating,
    WindowHeating,
)
from .models.auxiliary_heating import AuxiliaryConfig, AuxiliaryHeating, AuxiliaryHeatingTimer
from .models.charging import ChargeMode, Charging
from .models.chargingprofiles import ChargingProfiles
from .models.departure import DepartureInfo, DepartureTimer
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

type Vin = str


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


class MySkodaAuthorization(Authorization):
    client_id: str = CLIENT_ID  #  pyright: ignore[reportIncompatibleMethodOverride]
    redirect_uri: str = REDIRECT_URI  #  pyright: ignore[reportIncompatibleMethodOverride]
    base_url: str = BASE_URL_SKODA  #  pyright: ignore[reportIncompatibleMethodOverride]


class MySkoda:
    session: ClientSession
    rest_api: RestApi
    mqtt: MySkodaMqttClient | None = None
    authorization: MySkodaAuthorization
    ssl_context: SSLContext | None = None
    vehicles: dict[Vin, Vehicle]

    def __init__(  # noqa: D107, PLR0913
        self,
        session: ClientSession,
        ssl_context: SSLContext | None = None,
        mqtt_enabled: bool = True,
        mqtt_broker_host: str | None = None,
        mqtt_broker_port: int | None = None,
        mqtt_enable_ssl: bool | None = None,
    ) -> None:
        self.vehicles: dict[Vin, Vehicle] = {}
        self.session = session
        self.authorization = MySkodaAuthorization(session)
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
        try:
            async with timeout(MQTT_OPERATION_TIMEOUT):
                await self.mqtt.wait_for_operation(operation)
        except TimeoutError:
            _LOGGER.warning("Timeout occurred while waiting for %s. Aborted.", operation)

    async def connect(self, email: str, password: str) -> None:
        """Authenticate on the rest api and connect to the MQTT broker."""
        await self.authorization.authorize(email, password)
        _LOGGER.debug("IDK Authorization was successful.")

        if self.mqtt:
            user = await self.get_user()
            vehicles = await self.list_vehicle_vins()
            await self.mqtt.connect(user.id, vehicles)
        _LOGGER.debug("MySkoda ready.")

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

    async def set_auto_unlock_plug(self, vin: str, enabled: bool) -> None:
        """Enable or disable auto unlock plug when charged."""
        future = self._wait_for_operation(OperationName.UPDATE_AUTO_UNLOCK_PLUG)
        await self.rest_api.set_auto_unlock_plug(vin, enabled)
        await future

    async def set_charge_limit(self, vin: str, limit: int) -> None:
        """Set the maximum charge limit in percent."""
        future = self._wait_for_operation(OperationName.UPDATE_CHARGE_LIMIT)
        await self.rest_api.set_charge_limit(vin, limit)
        await future

    async def set_minimum_charge_limit(self, vin: str, limit: int) -> None:
        """Set minimum battery SoC in percent for departure timer."""
        future = self._wait_for_operation(OperationName.UPDATE_MINIMAL_SOC)
        await self.rest_api.set_minimum_charge_limit(vin, limit)
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

    async def set_ac_without_external_power(
        self, vin: str, settings: AirConditioningWithoutExternalPower
    ) -> None:
        """Enable or disable AC without external power."""
        future = self._wait_for_operation(OperationName.SET_AIR_CONDITIONING_WITHOUT_EXTERNAL_POWER)
        await self.rest_api.set_ac_without_external_power(vin, settings)
        await future

    async def set_ac_at_unlock(self, vin: str, settings: AirConditioningAtUnlock) -> None:
        """Enable or disable AC at unlock."""
        future = self._wait_for_operation(OperationName.SET_AIR_CONDITIONING_AT_UNLOCK)
        await self.rest_api.set_ac_at_unlock(vin, settings)
        await future

    async def set_windows_heating(self, vin: str, settings: WindowHeating) -> None:
        """Enable or disable windows heating with AC."""
        future = self._wait_for_operation(OperationName.WINDOWS_HEATING)
        await self.rest_api.set_windows_heating(vin, settings)
        await future

    async def set_seats_heating(self, vin: str, settings: SeatHeating) -> None:
        """Enable or disable seats heating with AC."""
        future = self._wait_for_operation(OperationName.SET_AIR_CONDITIONING_SEATS_HEATING)
        await self.rest_api.set_seats_heating(vin, settings)
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

    async def start_auxiliary_heating(
        self, vin: str, spin: str, config: AuxiliaryConfig | None = None
    ) -> None:
        """Start the auxiliary heating with the provided configuration."""
        future = self._wait_for_operation(OperationName.START_AUXILIARY_HEATING)
        await self.rest_api.start_auxiliary_heating(vin, spin, config=config)
        await future

    async def stop_auxiliary_heating(self, vin: str) -> None:
        """Stop the auxiliary heating."""
        future = self._wait_for_operation(OperationName.STOP_AUXILIARY_HEATING)
        await self.rest_api.stop_auxiliary_heating(vin)
        await future

    async def set_ac_timer(self, vin: str, timer: AirConditioningTimer) -> None:
        """Send provided air-conditioning timer to the vehicle."""
        future = self._wait_for_operation(OperationName.SET_AIR_CONDITIONING_TIMERS)
        await self.rest_api.set_ac_timer(vin, timer)
        await future

    async def set_auxiliary_heating_timer(
        self, vin: str, timer: AuxiliaryHeatingTimer, spin: str
    ) -> None:
        """Send provided auxiliary heating timer to the vehicle."""
        future = self._wait_for_operation(OperationName.SET_AIR_CONDITIONING_TIMERS)
        await self.rest_api.set_auxiliary_heating_timer(vin, timer, spin)
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

    async def set_departure_timer(self, vin: str, timer: DepartureTimer) -> None:
        """Send provided departure timer to the vehicle."""
        future = self._wait_for_operation(OperationName.UPDATE_DEPARTURE_TIMERS)
        await self.rest_api.set_departure_timer(vin, timer)
        await future

    async def get_departure_timers(self, vin: str, anonymize: bool = False) -> DepartureInfo:
        """Retrieve departure timers for the specified vehicle."""
        return (await self.rest_api.get_departure_timers(vin, anonymize=anonymize)).result

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

    async def get_charging_profiles(self, vin: str, anonymize: bool = False) -> ChargingProfiles:
        """Retrieve information related to charging profiles for the specified vehicle."""
        return (await self.rest_api.get_charging_profiles(vin, anonymize=anonymize)).result

    async def get_status(self, vin: str, anonymize: bool = False) -> Status:
        """Retrieve the current status for the specified vehicle."""
        return (await self.rest_api.get_status(vin, anonymize=anonymize)).result

    async def get_air_conditioning(self, vin: str, anonymize: bool = False) -> AirConditioning:
        """Retrieve the current air conditioning status for the specified vehicle."""
        return (await self.rest_api.get_air_conditioning(vin, anonymize=anonymize)).result

    async def get_auxiliary_heating(self, vin: str, anonymize: bool = False) -> AuxiliaryHeating:
        """Retrieve the current auxiliary heating status for the specified vehicle."""
        return (await self.rest_api.get_auxiliary_heating(vin, anonymize=anonymize)).result

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

    async def get_vehicle(
        self, vin: str, excluded_capabilities: list[CapabilityId] | None = None
    ) -> Vehicle:
        """Load a full vehicle based on its capabilities."""
        capabilities = [
            CapabilityId.AIR_CONDITIONING,
            CapabilityId.AUXILIARY_HEATING,
            CapabilityId.CHARGING,
            CapabilityId.PARKING_POSITION,
            CapabilityId.STATE,
            CapabilityId.TRIP_STATISTICS,
            CapabilityId.VEHICLE_HEALTH_INSPECTION,
            CapabilityId.DEPARTURE_TIMERS,
        ]

        if excluded_capabilities:
            capabilities = [c for c in capabilities if c not in excluded_capabilities]

        return await self.get_partial_vehicle(vin, capabilities)

    async def get_partial_vehicle(self, vin: str, capabilities: list[CapabilityId]) -> Vehicle:
        """Load a partial vehicle, based on list of capabilities."""
        info = await self.get_info(vin)
        maintenance = await self.get_maintenance(vin)

        if vin in self.vehicles:
            self.vehicles[vin].info = info
            self.vehicles[vin].maintenance = maintenance
        else:
            self.vehicles[vin] = Vehicle(info, maintenance)

        for capa in capabilities:
            if info.is_capability_available(capa):
                await self._request_capability_data(vin, capa)

        return deepcopy(self.vehicles[vin])

    async def _request_capability_data(self, vin: str, capa: CapabilityId) -> None:
        """Request specific capability data from MySkoda API."""
        try:
            match capa:
                case CapabilityId.AIR_CONDITIONING:
                    self.vehicles[vin].air_conditioning = await self.get_air_conditioning(vin)
                case CapabilityId.AUXILIARY_HEATING:
                    self.vehicles[vin].auxiliary_heating = await self.get_auxiliary_heating(vin)
                case CapabilityId.CHARGING:
                    self.vehicles[vin].charging = await self.get_charging(vin)
                case CapabilityId.PARKING_POSITION:
                    self.vehicles[vin].positions = await self.get_positions(vin)
                case CapabilityId.STATE:
                    self.vehicles[vin].status = await self.get_status(vin)
                    self.vehicles[vin].driving_range = await self.get_driving_range(vin)
                case CapabilityId.TRIP_STATISTICS:
                    self.vehicles[vin].trip_statistics = await self.get_trip_statistics(vin)
                case CapabilityId.VEHICLE_HEALTH_INSPECTION:
                    self.vehicles[vin].health = await self.get_health(vin)
                case CapabilityId.DEPARTURE_TIMERS:
                    self.vehicles[vin].departure_info = await self.get_departure_timers(vin)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Requesting %s failed: %s, continue", capa, err)

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
        # Mapping of endpoints to corresponding methods
        endpoint_method_map = {
            Endpoint.INFO: self.rest_api.get_info,
            Endpoint.STATUS: self.rest_api.get_status,
            Endpoint.AIR_CONDITIONING: self.rest_api.get_air_conditioning,
            Endpoint.AUXILIARY_HEATING: self.rest_api.get_auxiliary_heating,
            Endpoint.POSITIONS: self.rest_api.get_positions,
            Endpoint.HEALTH: self.rest_api.get_health,
            Endpoint.CHARGING: self.rest_api.get_charging,
            Endpoint.CHARGING_PROFILES: self.rest_api.get_charging_profiles,
            Endpoint.MAINTENANCE: self.rest_api.get_maintenance,
            Endpoint.DRIVING_RANGE: self.rest_api.get_driving_range,
            Endpoint.TRIP_STATISTICS: self.rest_api.get_trip_statistics,
            Endpoint.DEPARTURE_INFO: self.rest_api.get_departure_timers,
        }

        # Look up the method, or raise an error if unsupported
        method = endpoint_method_map.get(endpoint)
        if not method:
            error_message = f"Unsupported endpoint: {endpoint}"
            raise UnsupportedEndpointError(error_message)

        # Call the method and return the result
        return await method(vin, anonymize=anonymize)

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
            library_version=version,
        )


class MqttDisabledError(Exception):
    """MQTT was not enabled."""


class UnsupportedEndpointError(Exception):
    """Endpoint not implemented."""
