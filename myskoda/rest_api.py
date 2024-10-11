"""Contains API representation for the MySkoda REST API."""

import asyncio
import logging
from collections.abc import Callable

from aiohttp import ClientResponse, ClientResponseError, ClientSession

from .auth.authorization import Authorization
from .const import BASE_URL_SKODA, REQUEST_TIMEOUT_IN_SECONDS
from .models.air_conditioning import AirConditioning
from .models.charging import ChargeMode, Charging
from .models.driving_range import DrivingRange
from .models.garage import Garage
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

    async def _make_request(
        self, url: str, method: str, json: dict | None = None
    ) -> ClientResponse:
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT_IN_SECONDS):
                async with self.session.request(
                    method=method,
                    url=f"{BASE_URL_SKODA}/api{url}",
                    headers=await self._headers(),
                    json=json,
                ) as response:
                    response.raise_for_status()
                    await response.text()
                    return response
        except TimeoutError:
            _LOGGER.exception("Timeout while sending %s request to %s", method, url)
            raise
        except ClientResponseError as err:
            _LOGGER.exception("Invalid status for %s request to %s: %d", method, url, err.status)
            raise

    async def _make_get_request[T](self, url: str, deserialize: Callable[[str], T]) -> T:
        response = await self._make_request(url=url, method="GET")
        response_text = await response.text()
        try:
            data = deserialize(response_text)
        except Exception:
            _LOGGER.exception(
                "Failed to load data from url %s. Return value was '%s'", url, response_text
            )
            raise
        else:
            return data

    async def _make_post_request(self, url: str, json: dict | None = None) -> ClientResponse:
        return await self._make_request(url=url, method="POST", json=json)

    async def _make_put_request(self, url: str, json: dict | None = None) -> ClientResponse:
        return await self._make_request(url=url, method="PUT", json=json)

    async def get_info(self, vin: str) -> Info:
        """Retrieve the basic vehicle information for the specified vehicle."""
        return await self._make_get_request(
            f"/v2/garage/vehicles/{vin}?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
            Info.from_json,
        )

    async def get_charging(self, vin: str) -> Charging:
        """Retrieve information related to charging for the specified vehicle."""
        return await self._make_get_request(f"/v1/charging/{vin}", Charging.from_json)

    async def get_status(self, vin: str) -> Status:
        """Retrieve the current status for the specified vehicle."""
        return await self._make_get_request(f"/v2/vehicle-status/{vin}", Status.from_json)

    async def get_air_conditioning(self, vin: str) -> AirConditioning:
        """Retrieve the current air conditioning status for the specified vehicle."""
        return await self._make_get_request(
            f"/v2/air-conditioning/{vin}", AirConditioning.from_json
        )

    async def get_positions(self, vin: str) -> Positions:
        """Retrieve the current position for the specified vehicle."""
        return await self._make_get_request(f"/v1/maps/positions?vin={vin}", Positions.from_json)

    async def get_driving_range(self, vin: str) -> DrivingRange:
        """Retrieve estimated driving range for combustion vehicles."""
        return await self._make_get_request(
            f"/v2/vehicle-status/{vin}/driving-range", DrivingRange.from_json
        )

    async def get_trip_statistics(self, vin: str) -> TripStatistics:
        """Retrieve statistics about past trips."""
        return await self._make_get_request(
            f"/v1/trip-statistics/{vin}?offsetType=week&offset=0&timezone=Europe%2FBerlin",
            TripStatistics.from_json,
        )

    async def get_maintenance(self, vin: str) -> Maintenance:
        """Retrieve maintenance report."""
        return await self._make_get_request(
            f"/v3/vehicle-maintenance/vehicles/{vin}", Maintenance.from_json
        )

    async def get_health(self, vin: str) -> Health:
        """Retrieve health information for the specified vehicle."""
        return await self._make_get_request(
            f"/v1/vehicle-health-report/warning-lights/{vin}", Health.from_json
        )

    async def get_user(self) -> User:
        """Retrieve user information about logged in user."""
        return await self._make_get_request("/v1/users", User.from_json)

    async def list_vehicles(self) -> list[str]:
        """List all vehicles by their vins."""
        garage: Garage = await self._make_get_request(
            url="/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
            deserialize=Garage.from_json,
        )
        if garage.vehicles is None:
            return []
        return [vehicle.vin for vehicle in garage.vehicles]

    async def _headers(self) -> dict[str, str]:
        return {"authorization": f"Bearer {await self.authorization.get_access_token()}"}

    async def stop_air_conditioning(self, vin: str) -> None:
        """Stop the air conditioning."""
        _LOGGER.debug("Stopping air conditioning for vehicle %s", vin)
        await self._make_post_request(url=f"/v2/air-conditioning/{vin}/stop")

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
        await self._make_post_request(
            url=f"/v2/air-conditioning/{vin}/start",
            json=json_data,
        )

    async def set_target_temperature(self, vin: str, temperature: float) -> None:
        """Set the air conditioning's target temperature in °C."""
        _LOGGER.debug("Setting target temperature for vehicle %s to %s", vin, str(temperature))
        json_data = {"temperatureValue": str(temperature), "unitInCar": "CELSIUS"}
        await self._make_post_request(
            url=f"/v2/air-conditioning/{vin}/settings/target-temperature",
            json=json_data,
        )

    async def start_window_heating(self, vin: str) -> None:
        """Start heating both the front and rear window."""
        _LOGGER.debug("Starting window heating for vehicle %s", vin)
        await self._make_post_request(
            url=f"/v2/air-conditioning/{vin}/start-window-heating",
        )

    async def stop_window_heating(self, vin: str) -> None:
        """Stop heating both the front and rear window."""
        _LOGGER.debug("Stopping window heating for vehicle %s", vin)
        await self._make_post_request(
            url=f"/v2/air-conditioning/{vin}/stop-window-heating",
        )

    async def set_charge_limit(self, vin: str, limit: int) -> None:
        """Set the maximum charge limit in percent."""
        _LOGGER.debug("Setting charge limit for vehicle %s to %d", vin, limit)
        json_data = {"targetSOCInPercent": limit}
        await self._make_put_request(
            url=f"/v1/charging/{vin}/set-charge-limit",
            json=json_data,
        )

    # TODO @dvx76: Maybe refactor for FBT001
    async def set_battery_care_mode(self, vin: str, enabled: bool) -> None:
        """Enable or disable the battery care mode."""
        _LOGGER.debug("Setting battery care mode for vehicle %s to %r", vin, enabled)
        json_data = {"chargingCareMode": "ACTIVATED" if enabled else "DEACTIVATED"}
        await self._make_put_request(
            url=f"/v1/charging/{vin}/set-care-mode",
            json=json_data,
        )

    # TODO @dvx76: Maybe refactor for FBT001
    async def set_reduced_current_limit(self, vin: str, reduced: bool) -> None:
        """Enable reducing the current limit by which the car is charged."""
        _LOGGER.debug("Setting reduced charging for vehicle %s to %r", vin, reduced)
        json_data = {"chargingCurrent": "REDUCED" if reduced else "MAXIMUM"}
        await self._make_put_request(
            url=f"/v1/charging/{vin}/set-charging-current",
            json=json_data,
        )

    async def start_charging(self, vin: str) -> None:
        """Start charging the car."""
        _LOGGER.debug("Starting charging for vehicle %s", vin)
        await self._make_post_request(
            url=f"/v1/charging/{vin}/start",
        )

    async def stop_charging(self, vin: str) -> None:
        """Stop charging the car."""
        _LOGGER.debug("Stopping charging of vehicle %s", vin)
        await self._make_post_request(
            url=f"/v1/charging/{vin}/stop",
        )

    async def wakeup(self, vin: str) -> None:
        """Wake the vehicle up. Can be called maximum three times a day."""
        _LOGGER.debug("Waking up vehicle %s", vin)
        await self._make_post_request(
            url=f"/v1/vehicle-wakeup/{vin}?applyRequestLimiter=true",
        )

    async def set_charge_mode(self, vin: str, mode: ChargeMode) -> None:
        """Wake the vehicle up. Can be called maximum three times a day."""
        _LOGGER.debug("Changing charging mode of vehicle %s to %s", vin, mode)
        json_data = {"chargeMode": mode.value}
        await self._make_post_request(
            url=f"/v1/charging/{vin}/set-charge-mode",
            json=json_data,
        )

    # TODO @dvx76: Maybe refactor for FBT001
    async def honk_flash(
        self,
        vin: str,
        honk: bool = False,
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
        await self._make_post_request(
            url=f"/v1/vehicle-access/{vin}/honk-and-flash", json=json_data
        )
