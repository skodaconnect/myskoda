"""Contains API representation for the MySkoda REST API."""

from asyncio import gather
import logging

from aiohttp import ClientSession

from .authorization import IDKSession, idk_authorize
from .const import BASE_URL_SKODA
from .models.air_conditioning import AirConditioning
from .models.charging import Charging
from .models.health import Health
from .models.info import Info
from .models.status import Status

_LOGGER = logging.getLogger(__name__)


class Position:
    """Positional information (GPS) for the vehicle."""

    city: str
    country: str
    country_code: str
    house_number: str
    street: str
    zip_code: str
    lat: float
    lng: float

    def __init__(self, data):  # noqa: D107
        data = data.get("positions")[0]
        self.city = data.get("address", {}).get("city")
        self.country = data.get("address", {}).get("country")
        self.country_code = data.get("address", {}).get("countryCode")
        self.house_number = data.get("address", {}).get("houseNumber")
        self.street = data.get("address", {}).get("street")
        self.zip_code = data.get("address", {}).get("zipCode")
        self.lat = data.get("gpsCoordinates", {}).get("latitude")
        self.lng = data.get("gpsCoordinates", {}).get("longitude")


class Vehicle:
    """Wrapper class for all information from all endpoints."""

    info: Info
    charging: Charging
    status: Status
    air_conditioning: AirConditioning
    position: Position
    health: Health

    def __init__(  # noqa: D107
        self,
        info: Info,
        charging: Charging,
        status: Status,
        air_conditioning: AirConditioning,
        position: Position,
        health: Health,
    ):
        self.info = info
        self.charging = charging
        self.status = status
        self.air_conditioning = air_conditioning
        self.position = position
        self.health = health


class MySkodaHub:
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

    async def get_info(self, vin):
        """Retrieve the basic vehicle information for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/garage/vehicles/{vin}",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received basic info", vin)
            return Info(**await response.json())

    async def get_charging(self, vin):
        """Retrieve information related to charging for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}", headers=await self._headers()
        ) as response:
            _LOGGER.debug("Received charging info")
            return Charging(**await response.json())

    async def get_status(self, vin):
        """Retrieve the current status for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/vehicle-status/{vin}",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received status")
            return Status(**await response.json())

    async def get_air_conditioning(self, vin):
        """Retrieve the current air conditioning status for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received air conditioning")
            return AirConditioning(**await response.json())

    async def get_position(self, vin):
        """Retrieve the current position for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/maps/positions?vin={vin}",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received position")
            return Position(await response.json())

    async def get_health(self, vin):
        """Retrieve health information for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/vehicle-health-report/warning-lights/{vin}",
            headers=await self._headers(),
        ) as response:
            _LOGGER.debug("vin %s: Received health")
            return Health(**await response.json())

    async def list_vehicles(self):
        """List all vehicles by their vins."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/garage", headers=await self._headers()
        ) as response:
            json = await response.json()
            return [vehicle["vin"] for vehicle in json["vehicles"]]

    async def get_vehicle(self, vin) -> Vehicle:
        """Retrieve all information about a given vehicle by calling all endpoints."""
        [info, charging, status, air_conditioning, position, health] = await gather(
            *[
                self.get_info(vin),
                self.get_charging(vin),
                self.get_status(vin),
                self.get_air_conditioning(vin),
                self.get_position(vin),
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
        return await gather(
            *[self.get_vehicle(vehicle) for vehicle in await self.list_vehicles()]
        )

    async def _headers(self):
        return {
            "authorization": f"Bearer {await self.idk_session.get_access_token(self.session)}"
        }

    async def stop_air_conditioning(self, vin):
        """Stop the air conditioning."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/stop",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def start_air_conditioning(self, vin, temperature):
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

    async def set_target_temperature(self, vin, temperature):
        """Set the air conditioning's target temperature in °C."""
        json_data = {"temperatureValue": temperature, "unitInCar": "CELSIUS"}
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/settings/target-temperature",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    async def start_window_heating(self, vin):
        """Start heating both the front and rear window."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/start-window-heating",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def stop_window_heating(self, vin):
        """Stop heating both the front and rear window."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/stop-window-heating",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def set_charge_limit(self, vin, limit: int):
        """Set the maximum charge limit in percent."""
        json_data = {"targetSOCInPercent": limit}
        async with self.session.put(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/set-charge-limit",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    async def set_battery_care_mode(self, vin, enabled: bool):
        """Enable or disable the battery care mode."""
        json_data = {"chargingCareMode": "ACTIVATED" if enabled else "DEACTIVATED"}
        async with self.session.put(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/set-care-mode",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    async def set_reduced_current_limit(self, vin, reduced: bool):
        """Enable reducing the current limit by which the car is charged."""
        json_data = {"chargingCurrent": "REDUCED" if reduced else "MAXIMUM"}
        async with self.session.put(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/set-charging-current",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    async def start_charging(self, vin):
        """Start charging the car."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/start",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def stop_charging(self, vin):
        """Stop charging the car."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/stop",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def wakeup(self, vin):
        """Wake the vehicle up. Can be called maximum three times a day."""
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/vehicle-wakeup/{vin}?applyRequestLimiter=true",
            headers=await self._headers(),
        ) as response:
            await response.text()
