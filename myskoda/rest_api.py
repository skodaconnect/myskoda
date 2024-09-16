"""Contains API representation for the MySkoda REST API."""

import logging
from asyncio import gather

from aiohttp import ClientSession

from .authorization import IDKSession, idk_authorize
from .const import BASE_URL_SKODA
from .models.air_conditioning import AirConditioning
from .models.charging import Charging
from .models.driving_range import DrivingRange
from .models.health import Health
from .models.info import Info
from .models.maintenance import Maintenance
from .models.position import Positions, PositionType
from .models.status import Status
from .models.trip_statistics import TripStatistics

_LOGGER = logging.getLogger(__name__)


class Vehicle:
    """Wrapper class for all information from all endpoints."""

    info: Info
    charging: Charging
    status: Status
    air_conditioning: AirConditioning
    position: Positions
    health: Health

    def __init__(  # noqa: D107, PLR0913
        self,
        info: Info,
        charging: Charging,
        status: Status,
        air_conditioning: AirConditioning,
        position: Positions,
        health: Health,
    ) -> None:
        self.info = info
        self.charging = charging
        self.status = status
        self.air_conditioning = air_conditioning
        self.position = position
        self.health = health


class RestApi:
    """API hub class that can perform all calls to the MySkoda API."""

    session: ClientSession
    idk_session: IDKSession

    def __init__(self, session: ClientSession) -> None:  # noqa: D107
        self.session = session

    async def authenticate(self, email: str, password: str) -> bool:
        """Perform the full login process.

        Must be called before any other methods on the class can be called.
        """
        self.idk_session = await idk_authorize(self.session, email, password)

        _LOGGER.info("IDK Authorization was successful.")

        return True

    async def get_info(self, vin: str) -> Info:
        """Retrieve the basic vehicle information for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/garage/vehicles/{vin}?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received basic info", vin)
            return Info(**await response.json())

    async def get_charging(self, vin: str) -> Charging:
        """Retrieve information related to charging for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}", headers=await self._headers()
        ) as response:
            _LOGGER.debug("Received charging info")
            print(await response.json())
            return Charging(**await response.json())

    async def get_status(self, vin: str) -> Status:
        """Retrieve the current status for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/vehicle-status/{vin}",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received status")
            return Status(**await response.json())

    async def get_air_conditioning(self, vin: str) -> AirConditioning:
        """Retrieve the current air conditioning status for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received air conditioning")
            return AirConditioning(**await response.json())

    async def get_positions(self, vin: str) -> Positions:
        """Retrieve the current position for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/maps/positions?vin={vin}",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received position")
            return Positions(**await response.json())

    async def get_driving_range(self, vin: str) -> DrivingRange:
        """Retrieve estimated driving range for combustion vehicles."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/vehicle-status/{vin}/driving-range",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received driving range")
            return DrivingRange(**await response.json())

    async def get_trip_statistics(self, vin: str) -> TripStatistics:
        """Retrieve statistics about past trips."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/trip-statistics/{vin}?offsetType=week&offset=0&timezone=Europe%2FBerlin",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received trip statistics")
            return TripStatistics(**await response.json())

    async def get_maintenance(self, vin: str) -> Maintenance:
        """Retrieve maintenance report."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v3/vehicle-maintenance/vehicles/{vin}",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received maintenance report")
            return Maintenance(**await response.json())

    async def get_health(self, vin: str) -> Health:
        """Retrieve health information for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/vehicle-health-report/warning-lights/{vin}",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received health")
            return Health(**await response.json())

    async def list_vehicles(self) -> list[str]:
        """List all vehicles by their vins."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
            headers=await self._headers(),
        ) as response:
            json = await response.json()
            return [vehicle["vin"] for vehicle in json["vehicles"]]

    async def get_vehicle(self, vin: str) -> Vehicle:
        """Retrieve all information about a given vehicle by calling all endpoints."""
        [info, charging, status, air_conditioning, position, health] = await gather(
            *[
                self.get_info(vin),
                self.get_charging(vin),
                self.get_status(vin),
                self.get_air_conditioning(vin),
                self.get_positions(vin),
                self.get_health(vin),
            ]
        )
        return Vehicle(
            info=info,
            charging=charging,
            status=status,
            air_conditioning=air_conditioning,
            position=position,
            health=health,
        )

    async def get_all_vehicles(self) -> list[Vehicle]:
        """Call all endpoints for all vehicles in the user's garage."""
        return await gather(*[self.get_vehicle(vehicle) for vehicle in await self.list_vehicles()])

    async def _headers(self) -> dict[str, str]:
        return {"authorization": f"Bearer {await self.idk_session.get_access_token(self.session)}"}

    async def stop_air_conditioning(self, vin: str) -> None:
        """Stop the air conditioning."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/stop",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def start_air_conditioning(self, vin: str, temperature: str) -> None:
        """Start the air conditioning."""
        json_data = {
            "heaterSource": "ELECTRIC",
            "targetTemperature": {
                "temperatureValue": temperature,
                "unitInCar": "CELSIUS",
            },
        }
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/start",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    async def set_target_temperature(self, vin: str, temperature: str) -> None:
        """Set the air conditioning's target temperature in °C."""
        json_data = {"temperatureValue": temperature, "unitInCar": "CELSIUS"}
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/settings/target-temperature",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    async def start_window_heating(self, vin: str) -> None:
        """Start heating both the front and rear window."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/start-window-heating",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def stop_window_heating(self, vin: str) -> None:
        """Stop heating both the front and rear window."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/stop-window-heating",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def set_charge_limit(self, vin: str, limit: int) -> None:
        """Set the maximum charge limit in percent."""
        json_data = {"targetSOCInPercent": limit}
        async with self.session.put(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/set-charge-limit",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    # TODO @dvx76: Maybe refactor for FBT001
    async def set_battery_care_mode(self, vin: str, enabled: bool) -> None:  # noqa: FBT001
        """Enable or disable the battery care mode."""
        json_data = {"chargingCareMode": "ACTIVATED" if enabled else "DEACTIVATED"}
        async with self.session.put(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/set-care-mode",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    # TODO @dvx76: Maybe refactor for FBT001
    async def set_reduced_current_limit(self, vin: str, reduced: bool) -> None:  # noqa: FBT001
        """Enable reducing the current limit by which the car is charged."""
        json_data = {"chargingCurrent": "REDUCED" if reduced else "MAXIMUM"}
        async with self.session.put(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/set-charging-current",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    async def start_charging(self, vin: str) -> None:
        """Start charging the car."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/start",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def stop_charging(self, vin: str) -> None:
        """Stop charging the car."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/stop",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def wakeup(self, vin: str) -> None:
        """Wake the vehicle up. Can be called maximum three times a day."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/vehicle-wakeup/{vin}?applyRequestLimiter=true",
            headers=await self._headers(),
        ) as response:
            await response.text()

    # TODO @dvx76: Maybe refactor for FBT001
    async def honk_flash(self, vin: str, honk: bool = False) -> None:  # noqa: FBT001, FBT002
        """Honk and/or flash."""
        positions = await self.get_positions(vin)
        position = next(pos for pos in positions.positions if pos.type == PositionType.VEHICLE)
        json_data = {
            "mode": "HONK_AND_FLASH" if honk else "FLASH",
            "vehiclePosition": {
                "lat": position.gps_coordinates.latitude,
                "lng": position.gps_coordinates.longitude,
            },
        }
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/vehicle-access/{vin}/honk-and-flash",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()
