"""Unit tests for myskoda.rest_api."""

import json
from pathlib import Path

import pytest
from aioresponses import aioresponses

from myskoda.models.common import OpenState
from myskoda.models.status import DoorWindowState
from myskoda.models.trip_statistics import VehicleType
from myskoda.myskoda import MySkoda

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
async def test_get_info(
    vehicle_infos: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_info(). Needs more work."""
    for vehicle_info in vehicle_infos:
        vehicle_info_json = json.loads(vehicle_info)

        responses.get(
            url="https://mysmob.api.connect.skoda-auto.cz/api/v2/garage/vehicles/TMBJM0CKV1N12345"
            "?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3"
            "&connectivityGenerations=MOD4",
            body=vehicle_info,
        )

        get_info_result = await myskoda.get_info(vehicle_info_json["vin"])

        # Should probably assert the whole thing. Just an example.
        assert get_info_result.name == vehicle_info_json["name"]


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
async def test_get_status(
    vehicle_statuses: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_status(). Needs more work."""
    for vehicle_status in vehicle_statuses:
        vehicle_status_json = json.loads(vehicle_status)

        target_vin = "TMBJM0CKV1N12345"

        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/vehicle-status/{target_vin}",
            body=vehicle_status,
        )
        get_status_result = await myskoda.get_status(target_vin)

        assert get_status_result.overall.lights == vehicle_status_json["overall"]["lights"]
        assert get_status_result.overall.doors == vehicle_status_json["overall"]["doors"]
        assert get_status_result.detail.bonnet == vehicle_status_json["detail"]["bonnet"]
        assert get_status_result.detail.trunk == vehicle_status_json["detail"]["trunk"]


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
async def test_get_air_conditioning(
    air_conditioning: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_air_conditioning(). Needs more work."""
    for air_conditioning_status in air_conditioning:
        air_conditioning_status_json = json.loads(air_conditioning_status)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/air-conditioning/{target_vin}",
            body=air_conditioning_status,
        )
        get_status_result = await myskoda.get_air_conditioning(target_vin)

        assert get_status_result.state == air_conditioning_status_json["state"]
        assert (
            get_status_result.window_heating_state.front
            == air_conditioning_status_json["windowHeatingState"]["front"]
        )


@pytest.fixture(name="auxiliary_heating")
def load_auxiliary_heating() -> list[str]:
    """Load auxiliary_heating fixture."""
    auxiliary_heating = []
    for path in [
        "other/auxiliary-heating-idle.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            auxiliary_heating.append(file.read())
    return auxiliary_heating


@pytest.mark.asyncio
async def test_get_auxiliary_heating(
    auxiliary_heating: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_auxiliary_heating(). Needs more work."""
    for auxiliary_heating_status in auxiliary_heating:
        auxiliary_heating_status_json = json.loads(auxiliary_heating_status)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/air-conditioning/{target_vin}/auxiliary-heating",
            body=auxiliary_heating_status,
        )
        get_status_result = await myskoda.get_auxiliary_heating(target_vin)

        assert get_status_result.state == auxiliary_heating_status_json["state"]


@pytest.mark.asyncio
async def test_get_computed_status(myskoda: MySkoda, responses: aioresponses) -> None:
    """Test case for computed values of doors and windows state."""
    file_name = "superb/vehicle-status-left-back-door-trunk-bonnet-opened.json"
    vehicle_status = FIXTURES_DIR.joinpath(file_name).read_text()

    target_vin = "TMBJM0CKV1N12345"
    responses.get(
        url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/vehicle-status/{target_vin}",
        body=vehicle_status,
    )
    get_status_result = await myskoda.get_status(target_vin)

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
async def test_charging(charging: list[str], myskoda: MySkoda, responses: aioresponses) -> None:
    """Example unit test for RestAPI.charging(). Needs more work."""
    for charging_status in charging:
        air_conditioning_status_json = json.loads(charging_status)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v1/charging/{target_vin}",
            body=charging_status,
        )
        get_status_result = await myskoda.get_charging(target_vin)

        assert get_status_result.status is not None
        assert get_status_result.status.state == air_conditioning_status_json["status"]["state"]
        assert (
            get_status_result.settings.max_charge_current_ac
            == air_conditioning_status_json["settings"]["maxChargeCurrentAc"]
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
async def test_trip_statistics(
    trip_statistics: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.trip_statistics(). Needs more work."""
    for trip_statistics_input in trip_statistics:
        trip_statistics_json = json.loads(trip_statistics_input)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v1/trip-statistics/{target_vin}"
            "?offsetType=week&offset=0&timezone=Europe%2FBerlin",
            body=trip_statistics_input,
        )
        get_status_result = await myskoda.get_trip_statistics(target_vin)

        assert (
            get_status_result.overall_average_travel_time_in_min
            == trip_statistics_json["overallAverageTravelTimeInMin"]
        )
        assert get_status_result.vehicle_type == VehicleType.HYBRID


@pytest.fixture(name="spin_statuses")
def load_spin_status() -> list[str]:
    """Load spin-status fixture."""
    spin_statuses = []
    for path in [
        "superb/verify-spin-correct.json",
        "superb/verify-spin-incorrect.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            spin_statuses.append(file.read())
    return spin_statuses


@pytest.mark.asyncio
@pytest.mark.parametrize("spin", ["1234"])
async def test_get_spin_status(
    spin_statuses: list[str], myskoda: MySkoda, responses: aioresponses, spin: str
) -> None:
    """Example unit test for RestAPI.get_status(). Needs more work."""
    for spin_status in spin_statuses:
        spin_status_json = json.loads(spin_status)

        responses.post(
            url="https://mysmob.api.connect.skoda-auto.cz/api/v1/spin/verify",
            body=spin_status,
        )
        get_spin_status_result = await myskoda.verify_spin(spin)

        assert get_spin_status_result.verification_status == spin_status_json["verificationStatus"]
        if get_spin_status_result.spin_status is not None:
            assert (
                get_spin_status_result.spin_status.remaining_tries
                == spin_status_json["spinStatus"]["remainingTries"]
            )
            assert (
                get_spin_status_result.spin_status.locked_waiting_time_in_seconds
                == spin_status_json["spinStatus"]["lockedWaitingTimeInSeconds"]
            )
            assert (
                get_spin_status_result.spin_status.state == spin_status_json["spinStatus"]["state"]
            )
