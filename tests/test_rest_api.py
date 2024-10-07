"""Unit tests for myskoda.rest_api."""

import json
from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from myskoda import RestApi
from myskoda.auth.authorization import Authorization
from myskoda.models.common import OpenState
from myskoda.models.status import DoorWindowState
from myskoda.models.trip_statistics import VehicleType

FIXTURES_DIR = Path(__file__).parent.joinpath("fixtures")

print(f"__file__ = {__file__}")


@pytest.fixture(name="vehicle_infos")
def load_vehicle_info() -> list[str]:
    """Load vehicle-info fixture."""
    vehicle_infos = []
    # TODO @dvx76: probably just glob all files
    for path in [
        "enyaq/garage_vehicles_iv80.json",
        "enyaq/garage_vehicles_iv80_coupe.json",
        "superb/garage_vehicles_LK_liftback.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            vehicle_infos.append(file.read())
    return vehicle_infos


@pytest.mark.asyncio
async def test_get_info(vehicle_infos: list[str]) -> None:
    """Example unit test for RestAPI.get_info(). Needs more work."""
    for vehicle_info in vehicle_infos:
        vehicle_info_json = json.loads(vehicle_info)
        response_mock = AsyncMock()
        response_mock.text.return_value = vehicle_info
        session_mock = MagicMock()
        session_mock.get.return_value.__aenter__.return_value = response_mock

        authorization = Authorization(session_mock)
        api = RestApi(session_mock, authorization)
        api.authorization.get_access_token = AsyncMock()
        get_info_result = await api.get_info(vehicle_info_json["vin"])

        # Should probabaly assert the whole thing. Just an example.
        assert get_info_result.name == vehicle_info_json["name"]

        session_mock.get.assert_called_with(
            "https://mysmob.api.connect.skoda-auto.cz/api/v2/garage/vehicles/TMBJM0CKV1N12345"
            "?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3"
            "&connectivityGenerations=MOD4",
            headers=ANY,
        )


@pytest.fixture(name="vehicle_statuses")
def load_vehicle_status() -> list[str]:
    """Load vehicle-status fixture."""
    vehicle_statuses = []
    for path in [
        "superb/vehicle-status-doors-closed.json",
        "superb/vehicle-status-right-front-door-opened.json",
        "superb/vehicle-status-left-back-door-trunk-bonnet-opened.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            vehicle_statuses.append(file.read())
    return vehicle_statuses


@pytest.mark.asyncio
async def test_get_status(vehicle_statuses: list[str]) -> None:
    """Example unit test for RestAPI.get_status(). Needs more work."""
    for vehicle_status in vehicle_statuses:
        vehicle_status_json = json.loads(vehicle_status)
        response_mock = AsyncMock()
        response_mock.text.return_value = vehicle_status
        session_mock = MagicMock()
        session_mock.get.return_value.__aenter__.return_value = response_mock

        authorization = Authorization(session_mock)
        api = RestApi(session_mock, authorization)
        api.authorization.get_access_token = AsyncMock()
        target_vin = "TMBJM0CKV1N12345"
        get_status_result = await api.get_status(target_vin)

        assert get_status_result.overall.lights == vehicle_status_json["overall"]["lights"]
        assert get_status_result.overall.doors == vehicle_status_json["overall"]["doors"]
        assert get_status_result.detail.bonnet == vehicle_status_json["detail"]["bonnet"]
        assert get_status_result.detail.trunk == vehicle_status_json["detail"]["trunk"]

        session_mock.get.assert_called_with(
            f"https://mysmob.api.connect.skoda-auto.cz/api/v2/vehicle-status/{target_vin}",
            headers=ANY,
        )


@pytest.fixture(name="air_conditioning")
def load_air_conditioning() -> list[str]:
    """Load air-conditioning fixture."""
    air_conditioning = []
    for path in [
        "enyaq/air-conditioning-heating.json",
        "other/air-conditioning-idle.json",
        "superb/air-conditioning-aux-heater.json",
        "superb/air-conditioning-idle.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            air_conditioning.append(file.read())
    return air_conditioning


@pytest.mark.asyncio
async def test_get_air_conditioning(air_conditioning: list[str]) -> None:
    """Example unit test for RestAPI.get_air_conditioning(). Needs more work."""
    for air_conditioning_status in air_conditioning:
        air_conditioning_status_json = json.loads(air_conditioning_status)
        response_mock = AsyncMock()
        response_mock.text.return_value = air_conditioning_status
        session_mock = MagicMock()
        session_mock.get.return_value.__aenter__.return_value = response_mock

        authorization = Authorization(session_mock)
        api = RestApi(session_mock, authorization)
        api.authorization.get_access_token = AsyncMock()
        target_vin = "TMBJM0CKV1N12345"
        get_status_result = await api.get_air_conditioning(target_vin)

        assert get_status_result.state == air_conditioning_status_json["state"]
        assert (
            get_status_result.window_heating_state.front
            == air_conditioning_status_json["windowHeatingState"]["front"]
        )

        session_mock.get.assert_called_with(
            f"https://mysmob.api.connect.skoda-auto.cz/api/v2/air-conditioning/{target_vin}",
            headers=ANY,
        )


@pytest.mark.asyncio
async def test_get_computed_status() -> None:
    """Test case for computed values of doors and windows state."""
    file_name = "superb/vehicle-status-left-back-door-trunk-bonnet-opened.json"
    vehicle_status = FIXTURES_DIR.joinpath(file_name).read_text()
    response_mock = AsyncMock()
    response_mock.text.return_value = vehicle_status
    session_mock = MagicMock()
    session_mock.get.return_value.__aenter__.return_value = response_mock

    authorization = Authorization(session_mock)
    api = RestApi(session_mock, authorization)
    api.authorization.get_access_token = AsyncMock()
    target_vin = "TMBJM0CKV1N12345"
    get_status_result = await api.get_status(target_vin)

    assert get_status_result.left_front_door == DoorWindowState.CLOSED
    assert get_status_result.left_back_door == DoorWindowState.DOOR_OPEN
    assert get_status_result.right_front_door == DoorWindowState.CLOSED
    assert get_status_result.right_back_door == DoorWindowState.WINDOW_OPEN
    assert get_status_result.detail.bonnet == OpenState.OPEN
    assert get_status_result.detail.trunk == OpenState.OPEN


@pytest.fixture(name="charging")
def load_charging() -> list[str]:
    """Load charging fixture."""
    charging = []
    for path in [
        "superb/charging-iV.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            charging.append(file.read())
    return charging


@pytest.mark.asyncio
async def test_charging(charging: list[str]) -> None:
    """Example unit test for RestAPI.charging(). Needs more work."""
    for charging_status in charging:
        air_conditioning_status_json = json.loads(charging_status)
        response_mock = AsyncMock()
        response_mock.text.return_value = charging_status
        session_mock = MagicMock()
        session_mock.get.return_value.__aenter__.return_value = response_mock

        authorization = Authorization(session_mock)
        api = RestApi(session_mock, authorization)
        api.authorization.get_access_token = AsyncMock()
        target_vin = "TMBJM0CKV1N12345"
        get_status_result = await api.get_charging(target_vin)

        assert get_status_result.status is not None
        assert get_status_result.status.state == air_conditioning_status_json["status"]["state"]
        assert (
            get_status_result.settings.max_charge_current_ac
            == air_conditioning_status_json["settings"]["maxChargeCurrentAc"]
        )

        session_mock.get.assert_called_with(
            f"https://mysmob.api.connect.skoda-auto.cz/api/v1/charging/{target_vin}",
            headers=ANY,
        )


@pytest.fixture(name="trip_statistics")
def load_trip_statistics() -> list[str]:
    """Load trip statistics fixture."""
    trip_statistics = []
    for path in [
        "superb/trip-statistics-iV.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            trip_statistics.append(file.read())
    return trip_statistics


@pytest.mark.asyncio
async def test_trip_statistics(trip_statistics: list[str]) -> None:
    """Example unit test for RestAPI.trip_statistics(). Needs more work."""
    for trip_statistics_input in trip_statistics:
        trip_statistics_json = json.loads(trip_statistics_input)
        response_mock = AsyncMock()
        response_mock.text.return_value = trip_statistics_input
        session_mock = MagicMock()
        session_mock.get.return_value.__aenter__.return_value = response_mock

        authorization = Authorization(session_mock)
        api = RestApi(session_mock, authorization)
        api.authorization.get_access_token = AsyncMock()
        target_vin = "TMBJM0CKV1N12345"
        get_status_result = await api.get_trip_statistics(target_vin)

        assert (
            get_status_result.overall_average_travel_time_in_min
            == trip_statistics_json["overallAverageTravelTimeInMin"]
        )
        assert get_status_result.vehicle_type == VehicleType.HYBRID

        session_mock.get.assert_called_with(
            f"https://mysmob.api.connect.skoda-auto.cz/api/v1/trip-statistics/{target_vin}"
            "?offsetType=week&offset=0&timezone=Europe%2FBerlin",
            headers=ANY,
        )
