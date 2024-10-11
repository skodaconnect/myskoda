"""Contains API representation for the MySkoda REST API."""

import asyncio
import logging
from collections.abc import Callable

from aiohttp import ClientResponseError, ClientSession

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

    async def _make_request(self, url: str, method: str, json: dict | None = None) -> str:
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT_IN_SECONDS):
                async with self.session.request(
                    method=method,
                    url=f"{BASE_URL_SKODA}/api{url}",
                    headers=await self._headers(),
                    json=json,
                ) as response:
                    await response.text()  # Ensure response is fully read
                    response.raise_for_status()
                    return await response.text()
        except TimeoutError:
            _LOGGER.exception("Timeout while sending %s request to %s", method, url)
            raise
        except ClientResponseError as err:
            _LOGGER.exception("Invalid status for %s request to %s: %d", method, url, err.status)
            raise

    def _deserialize[T](self, text: str, deserialize: Callable[[str], T]) -> T:
        try:
            data = deserialize(text)
        except Exception:
            _LOGGER.exception("Failed to deserialize data: %s", text)
            raise
        else:
            return data

    async def _make_get_request[T](self, url: str) -> str:
        return await self._make_request(url=url, method="GET")

    async def _make_post_request(self, url: str, json: dict | None = None) -> str:
        return await self._make_request(url=url, method="POST", json=json)

    async def _make_put_request(self, url: str, json: dict | None = None) -> str:
        return await self._make_request(url=url, method="PUT", json=json)

    async def get_info_raw(self, vin: str) -> str:
        """Retrieve the basic vehicle information for the specified vehicle.

        This method will return the raw response as string.
        """
        return await self._make_get_request(
            f"/v2/garage/vehicles/{vin}?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
        )

    async def get_info(self, vin: str) -> Info:
        """Retrieve the basic vehicle information for the specified vehicle."""
        return self._deserialize(await self.get_info_raw(vin), Info.from_json)

    async def get_charging_raw(self, vin: str) -> str:
        """Retrieve the current status for the specified vehicle.

        This method will return the raw response as string.
        """
        return await self._make_get_request(f"/v1/charging/{vin}")

    async def get_charging(self, vin: str) -> Charging:
        """Retrieve information related to charging for the specified vehicle."""
        return self._deserialize(await self.get_charging_raw(vin), Charging.from_json)

    async def get_status_raw(self, vin: str) -> str:
        """Retrieve the current status for the specified vehicle.

        This method will return the raw response as string.
        """
        return await self._make_get_request(f"/v2/vehicle-status/{vin}")

    async def get_status(self, vin: str) -> Status:
        """Retrieve the current status for the specified vehicle."""
        return self._deserialize(await self.get_status_raw(vin), Status.from_json)

    async def get_air_conditioning_raw(self, vin: str) -> str:
        """Retrieve the current air conditioning status for the specified vehicle.

        This method will return the raw response as string.
        """
        return await self._make_get_request(f"/v2/air-conditioning/{vin}")

    async def get_air_conditioning(self, vin: str) -> AirConditioning:
        """Retrieve the current air conditioning status for the specified vehicle."""
        return self._deserialize(
            await self.get_air_conditioning_raw(vin), AirConditioning.from_json
        )

    async def get_positions_raw(self, vin: str) -> str:
        """Retrieve the current position for the specified vehicle.

        This method will return the raw response as string.
        """
        return await self._make_get_request(f"/v1/maps/positions?vin={vin}")

    async def get_positions(self, vin: str) -> Positions:
        """Retrieve the current position for the specified vehicle."""
        return self._deserialize(await self.get_positions_raw(vin), Positions.from_json)

    async def get_driving_range_raw(self, vin: str) -> str:
        """Retrieve estimated driving range for combustion vehicles.

        This method will return the raw response as string.
        """
        return await self._make_get_request(f"/v2/vehicle-status/{vin}/driving-range")

    async def get_driving_range(self, vin: str) -> DrivingRange:
        """Retrieve estimated driving range for combustion vehicles."""
        return self._deserialize(await self.get_driving_range_raw(vin), DrivingRange.from_json)

    async def get_trip_statistics_raw(self, vin: str) -> str:
        """Retrieve statistics about past trips.

        This method will return the raw response as string.
        """
        return await self._make_get_request(
            f"/v1/trip-statistics/{vin}?offsetType=week&offset=0&timezone=Europe%2FBerlin",
        )

    async def get_trip_statistics(self, vin: str) -> TripStatistics:
        """Retrieve statistics about past trips."""
        return self._deserialize(await self.get_trip_statistics_raw(vin), TripStatistics.from_json)

    async def get_maintenance_raw(self, vin: str) -> str:
        """Retrieve maintenance report.

        This method will return the raw response as string.
        """
        return await self._make_get_request(f"/v3/vehicle-maintenance/vehicles/{vin}")

    async def get_maintenance(self, vin: str) -> Maintenance:
        """Retrieve maintenance report."""
        return self._deserialize(await self.get_maintenance_raw(vin), Maintenance.from_json)

    async def get_health_raw(self, vin: str) -> str:
        """Retrieve health information for the specified vehicle.

        This method will return the raw response as string.
        """
        return await self._make_get_request(f"/v1/vehicle-health-report/warning-lights/{vin}")

    async def get_health(self, vin: str) -> Health:
        """Retrieve health information for the specified vehicle."""
        return self._deserialize(await self.get_health_raw(vin), Health.from_json)

    async def get_user_raw(self) -> str:
        """Retrieve user information about logged in user.

        This method will return the raw response as string.
        """
        return await self._make_get_request("/v1/users")

    async def get_user(self) -> User:
        """Retrieve user information about logged in user."""
        return self._deserialize(await self.get_user_raw(), User.from_json)

    async def get_garage(self) -> Garage:
        """Fetch the garage (list of vehicles with limited info)."""
        return self._deserialize(await self.get_garage_raw(), Garage.from_json)

    async def get_garage_raw(self) -> str:
        """Fetch the garage (list of vehicles with limited info).

        This method will return the raw response as string.
        """
        return await self._make_get_request(
            "/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
        )

    async def list_vehicles(self) -> list[str]:
        """List all vehicles by their vins."""
        garage = await self.get_garage()
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
