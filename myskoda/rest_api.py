"""Contains API representation for the MySkoda REST API."""

import logging

from aiohttp import ClientSession

from .auth.authorization import Authorization
from .const import BASE_URL_SKODA
from .models.air_conditioning import AirConditioning
from .models.charging import ChargeMode, Charging
from .models.driving_range import DrivingRange
from .models.health import Health
from .models.info import Info
from .models.maintenance import Maintenance
from .models.position import Positions, PositionType
from .models.status import Status
from .models.trip_statistics import TripStatistics
from .models.user import User

_LOGGER = logging.getLogger(__name__)


class RestApi:
    """API hub class that can perform all calls to the MySkoda API."""

    session: ClientSession
    authorization: Authorization

    def __init__(self, session: ClientSession, authorization: Authorization) -> None:  # noqa: D107
        self.session = session
        self.authorization = authorization

    async def get_info(self, vin: str) -> Info:
        """Retrieve the basic vehicle information for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/garage/vehicles/{vin}?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
            headers=await self._headers(),
        ) as response:
            response_text = await response.text()
            _LOGGER.debug(f"vin {vin}: received basic info: {response_text}")
            return Info.parse_raw(response_text)

    async def get_charging(self, vin: str) -> Charging:
        """Retrieve information related to charging for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}", headers=await self._headers()
        ) as response:
            response_text = await response.text()
            _LOGGER.debug(f"vin {vin}: received charging info: {response_text}")
            return Charging.parse_raw(response_text)

    async def get_status(self, vin: str) -> Status:
        """Retrieve the current status for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/vehicle-status/{vin}",
            headers=await self._headers(),
        ) as response:
            response_text = await response.text()
            _LOGGER.debug(f"vin {vin}: received status: {response_text}")
            return Status.parse_raw(response_text)

    async def get_air_conditioning(self, vin: str) -> AirConditioning:
        """Retrieve the current air conditioning status for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}",
            headers=await self._headers(),
        ) as response:
            response_text = await response.text()
            _LOGGER.debug(f"vin {vin}: received air conditioning: {response_text}")
            return AirConditioning.parse_raw(response_text)

    async def get_positions(self, vin: str) -> Positions:
        """Retrieve the current position for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/maps/positions?vin={vin}",
            headers=await self._headers(),
        ) as response:
            response_text = await response.text()
            _LOGGER.debug(f"vin {vin}: received position: {response_text}")
            return Positions.parse_raw(response_text)

    async def get_driving_range(self, vin: str) -> DrivingRange:
        """Retrieve estimated driving range for combustion vehicles."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/vehicle-status/{vin}/driving-range",
            headers=await self._headers(),
        ) as response:
            response_text = await response.text()
            _LOGGER.debug(f"vin {vin}: received driving range: {response_text}")
            return DrivingRange.parse_raw(response_text)

    async def get_trip_statistics(self, vin: str) -> TripStatistics:
        """Retrieve statistics about past trips."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/trip-statistics/{vin}?offsetType=week&offset=0&timezone=Europe%2FBerlin",
            headers=await self._headers(),
        ) as response:
            response_text = await response.text()
            _LOGGER.debug(f"vin {vin}: received trip statistics: {response_text}")
            return TripStatistics.parse_raw(response_text)

    async def get_maintenance(self, vin: str) -> Maintenance:
        """Retrieve maintenance report."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v3/vehicle-maintenance/vehicles/{vin}",
            headers=await self._headers(),
        ) as response:
            response_text = await response.text()
            _LOGGER.debug(f"vin {vin}: received maintenance report: {response_text}")
            return Maintenance.parse_raw(response_text)

    async def get_health(self, vin: str) -> Health:
        """Retrieve health information for the specified vehicle."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/vehicle-health-report/warning-lights/{vin}",
            headers=await self._headers(),
        ) as response:
            response_text = await response.text()
            _LOGGER.debug(f"vin {vin}: received health: {response_text}")
            return Health.parse_raw(response_text)

    async def get_user(self) -> User:
        """Retrieve user information about logged in user."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v1/users",
            headers=await self._headers(),
        ) as response:
            response_text = await response.text()
            _LOGGER.debug(f"received user: {response_text}")
            return User.parse_raw(response_text)

    async def list_vehicles(self) -> list[str]:
        """List all vehicles by their vins."""
        async with self.session.get(
            f"{BASE_URL_SKODA}/api/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
            headers=await self._headers(),
        ) as response:
            json = await response.json()
            return [vehicle["vin"] for vehicle in json["vehicles"]]

    async def _headers(self) -> dict[str, str]:
        return {"authorization": f"Bearer {await self.authorization.get_access_token()}"}

    async def stop_air_conditioning(self, vin: str) -> None:
        """Stop the air conditioning."""
        _LOGGER.debug("Stopping air conditioning for vehicle %s", vin)
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/stop",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def start_air_conditioning(self, vin: str, temperature: float) -> None:
        """Start the air conditioning."""
        _LOGGER.debug(
            "Starting air conditioning for vehicle %s with temperature %s",
            vin,
            str(temperature),
        )
        json_data = {
            "heaterSource": "ELECTRIC",
            "targetTemperature": {
                "temperatureValue": str(temperature),
                "unitInCar": "CELSIUS",
            },
        }
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/start",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    async def set_target_temperature(self, vin: str, temperature: float) -> None:
        """Set the air conditioning's target temperature in °C."""
        _LOGGER.debug("Setting target temperature for vehicle %s to %s", vin, str(temperature))
        json_data = {"temperatureValue": str(temperature), "unitInCar": "CELSIUS"}
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/settings/target-temperature",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    async def start_window_heating(self, vin: str) -> None:
        """Start heating both the front and rear window."""
        _LOGGER.debug("Starting window heating for vehicle %s", vin)
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/start-window-heating",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def stop_window_heating(self, vin: str) -> None:
        """Stop heating both the front and rear window."""
        _LOGGER.debug("Stopping window heating for vehicle %s", vin)
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v2/air-conditioning/{vin}/stop-window-heating",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def set_charge_limit(self, vin: str, limit: int) -> None:
        """Set the maximum charge limit in percent."""
        _LOGGER.debug("Setting charge limit for vehicle %s to %d", vin, limit)
        json_data = {"targetSOCInPercent": limit}
        async with self.session.put(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/set-charge-limit",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    # TODO @dvx76: Maybe refactor for FBT001
    async def set_battery_care_mode(self, vin: str, enabled: bool) -> None:
        """Enable or disable the battery care mode."""
        _LOGGER.debug("Setting battery care mode for vehicle %s to %r", vin, enabled)
        json_data = {"chargingCareMode": "ACTIVATED" if enabled else "DEACTIVATED"}
        async with self.session.put(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/set-care-mode",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    # TODO @dvx76: Maybe refactor for FBT001
    async def set_reduced_current_limit(self, vin: str, reduced: bool) -> None:
        """Enable reducing the current limit by which the car is charged."""
        _LOGGER.debug("Setting reduced charging for vehicle %s to %r", vin, reduced)
        json_data = {"chargingCurrent": "REDUCED" if reduced else "MAXIMUM"}
        async with self.session.put(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/set-charging-current",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    async def start_charging(self, vin: str) -> None:
        """Start charging the car."""
        _LOGGER.debug("Starting charging for vehicle %s", vin)
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/start",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def stop_charging(self, vin: str) -> None:
        """Stop charging the car."""
        _LOGGER.debug("Stopping charging of vehicle %s", vin)
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/stop",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def wakeup(self, vin: str) -> None:
        """Wake the vehicle up. Can be called maximum three times a day."""
        _LOGGER.debug("Waking up vehicle %s", vin)
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/vehicle-wakeup/{vin}?applyRequestLimiter=true",
            headers=await self._headers(),
        ) as response:
            await response.text()

    async def set_charge_mode(self, vin: str, mode: ChargeMode) -> None:
        """Wake the vehicle up. Can be called maximum three times a day."""
        _LOGGER.debug("Changing charging mode of vehicle %s to %s", vin, mode)
        json_data = {"chargeMode": mode.value}
        async with self.session.post(
            f"{BASE_URL_SKODA}/api/v1/charging/{vin}/set-charge-mode",
            headers=await self._headers(),
            json=json_data,
        ) as response:
            await response.text()

    # TODO @dvx76: Maybe refactor for FBT001
    async def honk_flash(
        self,
        vin: str,
        honk: bool = False,  # noqa:FBT002
    ) -> None:
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
