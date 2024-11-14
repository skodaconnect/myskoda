"""Contains API representation for the MySkoda REST API."""

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass

from aiohttp import ClientResponseError, ClientSession

from myskoda.anonymize import (
    anonymize_air_conditioning,
    anonymize_charging,
    anonymize_driving_range,
    anonymize_garage,
    anonymize_health,
    anonymize_info,
    anonymize_maintenance,
    anonymize_positions,
    anonymize_status,
    anonymize_trip_statistics,
    anonymize_url,
    anonymize_user,
)
from myskoda.models.charging import ChargeMode
from myskoda.models.garage import Garage
from myskoda.models.position import Position, PositionType

from .auth.authorization import Authorization
from .const import BASE_URL_SKODA, REQUEST_TIMEOUT_IN_SECONDS
from .models.air_conditioning import AirConditioning
from .models.charging import Charging
from .models.driving_range import DrivingRange
from .models.health import Health
from .models.info import Info
from .models.maintenance import Maintenance
from .models.position import Positions
from .models.spin import Spin
from .models.status import Status
from .models.trip_statistics import TripStatistics
from .models.user import User

_LOGGER = logging.getLogger(__name__)


@dataclass
class GetEndpointResult[T]:
    url: str
    raw: str
    result: T


class RestApi:
    """API hub class that can perform all calls to the MySkoda API."""

    session: ClientSession
    authorization: Authorization

    def __init__(self, session: ClientSession, authorization: Authorization) -> None:  # noqa: D107
        self.session = session
        self.authorization = authorization

    def process_json(
        self,
        data: str,
        anonymize: bool,
        anonymization_fn: Callable[[dict], dict],
    ) -> str:
        """Process the raw json returned by the API with some preprocessor logic."""
        if not anonymize:
            return data
        parsed = json.loads(data)
        anonymized = anonymization_fn(parsed)
        return json.dumps(anonymized)

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

    async def _make_get_request[T](self, url: str) -> str:
        return await self._make_request(url=url, method="GET")

    async def _make_post_request(self, url: str, json: dict | None = None) -> str:
        return await self._make_request(url=url, method="POST", json=json)

    async def _make_put_request(self, url: str, json: dict | None = None) -> str:
        return await self._make_request(url=url, method="PUT", json=json)

    async def verify_spin(self, spin: str, anonymize: bool = False) -> GetEndpointResult[Spin]:
        """Verify SPIN."""
        url = "/v1/spin/verify"
        json_data = {"currentSpin": spin}
        raw = self.process_json(
            data=await self._make_post_request(url, json_data),
            anonymize=anonymize,
            anonymization_fn=anonymize_info,
        )
        result = self._deserialize(raw, Spin.from_json)
        url = anonymize_url(url) if anonymize else url
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_info(self, vin: str, anonymize: bool = False) -> GetEndpointResult[Info]:
        """Retrieve information related to basic information for the specified vehicle."""
        url = f"/v2/garage/vehicles/{vin}?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4"  # noqa: E501
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_info,
        )
        result = self._deserialize(raw, Info.from_json)
        url = anonymize_url(url) if anonymize else url
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_charging(self, vin: str, anonymize: bool = False) -> GetEndpointResult[Charging]:
        """Retrieve information related to charging for the specified vehicle."""
        url = f"/v1/charging/{vin}"
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_charging,
        )
        result = self._deserialize(raw, Charging.from_json)
        url = anonymize_url(url) if anonymize else url
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_status(self, vin: str, anonymize: bool = False) -> GetEndpointResult[Status]:
        """Retrieve the current status for the specified vehicle."""
        url = f"/v2/vehicle-status/{vin}"
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_status,
        )
        result = self._deserialize(raw, Status.from_json)
        url = anonymize_url(url) if anonymize else url
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_air_conditioning(
        self, vin: str, anonymize: bool = False
    ) -> GetEndpointResult[AirConditioning]:
        """Retrieve the current air conditioning status for the specified vehicle."""
        url = f"/v2/air-conditioning/{vin}"
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_air_conditioning,
        )
        result = self._deserialize(raw, AirConditioning.from_json)
        url = anonymize_url(url) if anonymize else url
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_positions(
        self, vin: str, anonymize: bool = False
    ) -> GetEndpointResult[Positions]:
        """Retrieve the current position for the specified vehicle."""
        url = f"/v1/maps/positions?vin={vin}"
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_positions,
        )
        result = self._deserialize(raw, Positions.from_json)
        url = anonymize_url(url) if anonymize else url
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_driving_range(
        self, vin: str, anonymize: bool = False
    ) -> GetEndpointResult[DrivingRange]:
        """Retrieve estimated driving range for combustion vehicles."""
        url = f"/v2/vehicle-status/{vin}/driving-range"
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_driving_range,
        )
        result = self._deserialize(raw, DrivingRange.from_json)
        url = anonymize_url(url) if anonymize else url
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_trip_statistics(
        self, vin: str, anonymize: bool = False
    ) -> GetEndpointResult[TripStatistics]:
        """Retrieve statistics about past trips."""
        url = f"/v1/trip-statistics/{vin}?offsetType=week&offset=0&timezone=Europe%2FBerlin"
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_trip_statistics,
        )
        result = self._deserialize(raw, TripStatistics.from_json)
        url = anonymize_url(url) if anonymize else url
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_maintenance(
        self, vin: str, anonymize: bool = False
    ) -> GetEndpointResult[Maintenance]:
        """Retrieve maintenance report."""
        url = f"/v3/vehicle-maintenance/vehicles/{vin}"
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_maintenance,
        )
        result = self._deserialize(raw, Maintenance.from_json)
        url = anonymize_url(url) if anonymize else url
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_health(self, vin: str, anonymize: bool = False) -> GetEndpointResult[Health]:
        """Retrieve health information for the specified vehicle."""
        url = f"/v1/vehicle-health-report/warning-lights/{vin}"
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_health,
        )
        result = self._deserialize(raw, Health.from_json)
        url = anonymize_url(url) if anonymize else url
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_user(self, anonymize: bool = False) -> GetEndpointResult[User]:
        """Retrieve user information about logged in user."""
        url = "/v1/users"
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_user,
        )
        result = self._deserialize(raw, User.from_json)
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def get_garage(self, anonymize: bool = False) -> GetEndpointResult[Garage]:
        """Fetch the garage (list of vehicles with limited info)."""
        url = "/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4"  # noqa: E501
        raw = self.process_json(
            data=await self._make_get_request(url),
            anonymize=anonymize,
            anonymization_fn=anonymize_garage,
        )
        result = self._deserialize(raw, Garage.from_json)
        return GetEndpointResult(url=url, raw=raw, result=result)

    async def _headers(self) -> dict[str, str]:
        return {"authorization": f"Bearer {await self.authorization.get_access_token()}"}

    async def stop_air_conditioning(self, vin: str) -> None:
        """Stop the air conditioning."""
        _LOGGER.debug("Stopping air conditioning for vehicle %s", vin)
        await self._make_post_request(url=f"/v2/air-conditioning/{vin}/stop")

    async def start_air_conditioning(self, vin: str, temperature: float) -> None:
        """Start the air conditioning."""
        round_temp = f"{round(temperature * 2) / 2:.1f}"
        _LOGGER.debug(
            "Starting air conditioning for vehicle %s with temperature %s",
            vin,
            round_temp,
        )
        json_data = {
            "heaterSource": "ELECTRIC",
            "targetTemperature": {
                "temperatureValue": round_temp,
                "unitInCar": "CELSIUS",
            },
        }
        await self._make_post_request(
            url=f"/v2/air-conditioning/{vin}/start",
            json=json_data,
        )

    async def stop_auxiliary_heating(self, vin: str) -> None:
        """Stop the auxiliary heating."""
        _LOGGER.debug("Stopping auxiliary heating for vehicle %s", vin)
        await self._make_post_request(url=f"/v2/air-conditioning/{vin}/auxiliary-heating/stop")

    async def start_auxiliary_heating(self, vin: str, temperature: float, spin: str) -> None:
        """Start the auxiliary heating."""
        round_temp = f"{round(temperature * 2) / 2:.1f}"
        _LOGGER.debug(
            "Starting auxiliary heating for vehicle %s with temperature %s",
            vin,
            round_temp,
        )
        json_data = {
            "heaterSource": "AUTOMATIC",
            "airConditioningWithoutExternalPower": True,
            "spin": spin,
            "targetTemperature": {
                "temperatureValue": round_temp,
                "unitInCar": "CELSIUS",
            },
        }
        await self._make_post_request(
            url=f"/v2/air-conditioning/{vin}/auxiliary-heating/start",
            json=json_data,
        )

    async def set_target_temperature(self, vin: str, temperature: float) -> None:
        """Set the air conditioning's target temperature in °C."""
        round_temp = f"{round(temperature * 2) / 2:.1f}"
        _LOGGER.debug("Setting target temperature for vehicle %s to %s", vin, round_temp)
        json_data = {"temperatureValue": round_temp, "unitInCar": "CELSIUS"}
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

    async def lock(self, vin: str, spin: str) -> None:
        """Lock the vehicle."""
        _LOGGER.debug("Locking vehicle %s", vin)
        json_data = {"currentSpin": spin}
        await self._make_post_request(
            url=f"/v1/vehicle-access/{vin}/lock",
            json=json_data,
        )

    async def unlock(self, vin: str, spin: str) -> None:
        """Unlock the vehicle."""
        _LOGGER.debug("Unlocking vehicle %s", vin)
        json_data = {"currentSpin": spin}
        await self._make_post_request(
            url=f"/v1/vehicle-access/{vin}/unlock",
            json=json_data,
        )

    # TODO @dvx76: Maybe refactor for FBT001
    async def honk_flash(
        self,
        vin: str,
        positions: list[Position],
    ) -> None:
        """Emit Honk and flash."""
        position = next(pos for pos in positions if pos.type == PositionType.VEHICLE)
        # TODO @webspider: Make this a proper class
        json_data = {
            "mode": "HONK_AND_FLASH",
            "vehiclePosition": {
                "latitude": position.gps_coordinates.latitude,
                "longitude": position.gps_coordinates.longitude,
            },
        }
        await self._make_post_request(
            url=f"/v1/vehicle-access/{vin}/honk-and-flash", json=json_data
        )

    async def flash(
        self,
        vin: str,
        positions: list[Position],
    ) -> None:
        """Emit flash."""
        position = next(pos for pos in positions if pos.type == PositionType.VEHICLE)
        # TODO @webspider: Make this a proper class
        json_data = {
            "mode": "FLASH",
            "vehiclePosition": {
                "latitude": position.gps_coordinates.latitude,
                "longitude": position.gps_coordinates.longitude,
            },
        }
        await self._make_post_request(
            url=f"/v1/vehicle-access/{vin}/honk-and-flash", json=json_data
        )

    def _deserialize[T](self, text: str, deserialize: Callable[[str], T]) -> T:
        try:
            data = deserialize(text)
        except Exception:
            _LOGGER.exception("Failed to deserialize data: %s", text)
            raise
        else:
            return data
