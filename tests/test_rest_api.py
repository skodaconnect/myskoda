"""Unit tests for myskoda.rest_api."""

import json
import re
from collections.abc import Callable
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pytest
from aiohttp import ClientResponseError
from aioresponses import aioresponses

from myskoda.anonymize import FORMATTED_ADDRESS, LICENSE_PLATE, LOCATION, VEHICLE_NAME, VIN
from myskoda.models.common import OpenState
from myskoda.models.departure import DepartureInfo
from myskoda.models.driving_score import DrivingScoreResult
from myskoda.models.status import DoorWindowState
from myskoda.models.trip_statistics import VehicleType
from myskoda.models.widget import (
    ParkingPositionInMotion,
    ParkingPositionParked,
    ParkingPositionState,
)
from myskoda.myskoda import MySkoda
from myskoda.rest_api import RestApi
from myskoda.utils import to_iso8601

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
        "superb/garage_with_429_error.json",
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
        "superb/vehicle-status-unknown.json",
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
        "enyaq/air-conditioning-no-steering.json",
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
            get_status_result.window_heating_state is None
            or get_status_result.window_heating_state.front
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


@pytest.fixture(name="charging_profiles")
def load_chargingprofiles() -> list[str]:
    """Load charging profile fixture."""
    charging_profiles = []
    for path in [
        "enyaq/charging-profiles.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            charging_profiles.append(file.read())
    return charging_profiles


@pytest.mark.asyncio
async def test_charging_profiles(
    charging_profiles: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    for charging_profile in charging_profiles:
        charging_profile_status_json = json.loads(charging_profile)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v1/charging/{target_vin}/profiles",
            body=charging_profile,
        )
        get_status_result = await myskoda.get_charging_profiles(target_vin)

        assert get_status_result.charging_profiles is not None
        assert (
            get_status_result.charging_profiles[0].id
            == charging_profile_status_json["chargingProfiles"][0]["id"]
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


@pytest.fixture(name="vehicle_connection_statuses")
def load_vehicle_connection_status() -> list[str]:
    """Load connection status fixture."""
    vehicle_connection_statuses = []
    for path in [
        "other/vehicle-connection-status.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            vehicle_connection_statuses.append(file.read())
    return vehicle_connection_statuses


@pytest.mark.asyncio
async def test_vehicle_connection_status(
    vehicle_connection_statuses: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Unit test for RestAPI.get_connection_status(). Needs more work."""
    for connection_status in vehicle_connection_statuses:
        connection_status_json = json.loads(connection_status)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/connection-status/{target_vin}/readiness",
            body=connection_status,
        )
        get_connection_status = await myskoda.get_connection_status(target_vin)

        assert get_connection_status.unreachable == connection_status_json["unreachable"]
        assert get_connection_status.in_motion == connection_status_json["inMotion"]
        assert (
            get_connection_status.battery_protection_limit_on
            == connection_status_json["batteryProtectionLimitOn"]
        )


@pytest.fixture(name="charging_histories")
def load_charging_histories() -> list[str]:
    """Load charging history fixtures."""
    charging_histories = []
    for path in [
        "other/charging-history.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            charging_histories.append(file.read())
    return charging_histories


@pytest.mark.asyncio
async def test_charging_history(
    charging_histories: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Unit test for RestAPI.get_charging_history(). Needs more work."""
    for charging_history in charging_histories:
        charging_history_json = json.loads(charging_history)

        target_vin = "TMBJM0CKV1N12345"
        request_limit: int = 50
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v1/charging/{target_vin}/history?userTimezone=UTC&limit={request_limit}",
            body=charging_history,
        )

        get_charging_history = await myskoda.get_charging_history(target_vin)
        # Make sure the cursor is correct
        if get_charging_history.next_cursor:
            assert (
                to_iso8601(get_charging_history.next_cursor) == charging_history_json["nextCursor"]
            )
        # Make sure we dont get more than we asked for
        assert (
            len([session for period in get_charging_history.periods for session in period.sessions])
            < request_limit + 1
        )
        assert len(get_charging_history.periods) > 0


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


@pytest.fixture(name="departure_timers")
def load_departure_timers() -> list[str]:
    """Load departure timers fixture."""
    departure_timers = []
    for path in [
        "other/departure-timers.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            departure_timers.append(file.read())
    return departure_timers


@pytest.mark.asyncio
async def test_get_departure_timers(
    departure_timers: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.charging(). Needs more work."""
    for departure_timer in departure_timers:
        target_vin = "TMBJM0CKV1N12345"
        base_url = f"https://mysmob.api.connect.skoda-auto.cz/api/v1/vehicle-automatization/{target_vin}/departure/timers"
        # Add a regular expression for the dynamic timestamp query parameter
        url_pattern = re.compile(rf"{base_url}\?deviceDateTime=.*")

        responses.get(
            url=url_pattern,
            body=departure_timer,
        )

        with patch("myskoda.models.common.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
            get_departure_timers_result = await myskoda.get_departure_timers(target_vin)

            assert get_departure_timers_result == DepartureInfo.from_json(departure_timer)


@pytest.fixture(name="single_trips")
def load_single_trips() -> list[str]:
    """Load single trips fixture."""
    single_trips = []
    for path in [
        "superb/single-trips-iV.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            single_trips.append(file.read())
    return single_trips


@pytest.mark.asyncio
async def test_single_trips(
    single_trips: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.single_trips(). Needs more work."""
    for single_trips_input in single_trips:
        single_trips_json = json.loads(single_trips_input)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v1/trip-statistics/{target_vin}"
            "/single-trips?timezone=Europe%2FBerlin",
            body=single_trips_input,
        )
        get_single_trip_result = await myskoda.get_single_trip_statistics(target_vin)

        overall_cost = get_single_trip_result.daily_trips[0].overall_cost
        assert overall_cost is not None

        assert (
            overall_cost.total_cost
            == single_trips_json["dailyTrips"][0]["overallCost"]["totalCost"]
        )

        day2 = get_single_trip_result.daily_trips[1]
        assert day2.date == single_trips_json["dailyTrips"][1]["date"]
        assert day2.trips is not None
        assert len(day2.trips) == len(single_trips_json["dailyTrips"][1]["trips"])
        assert day2.trips[0].end_time == single_trips_json["dailyTrips"][1]["trips"][0]["endTime"]

        assert get_single_trip_result.vehicle_type == VehicleType.FUEL


@pytest.fixture(name="software_updates")
def load_software_updates() -> list[str]:
    """Load software updates fixture."""
    software_updates = []
    for path in [
        "enyaq/software-version.json",
        "enyaq/software-version-no-update.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            software_updates.append(file.read())
    return software_updates


@pytest.mark.asyncio
async def test_software_updates(
    software_updates: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.software_updates(). Needs more work."""
    for software_updates_input in software_updates:
        software_updates_json = json.loads(software_updates_input)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v1/vehicle-information/{target_vin}/software-version/update-status",
            body=software_updates_input,
        )
        get_software_version_result = await myskoda.get_software_update_status(target_vin)

        assert get_software_version_result.status == software_updates_json["status"]
        if "releaseNotesUrl" in software_updates_json:
            assert (
                get_software_version_result.release_notes_url
                == software_updates_json["releaseNotesUrl"]
            )
        assert (
            get_software_version_result.current_software_version
            == software_updates_json["currentSoftwareVersion"]
        )


@pytest.fixture(name="driving_score")
def load_driving_score() -> list[str]:
    """Load driving score fixture."""
    driving_score = []
    for path in [
        "superb/driving-score.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            driving_score.append(file.read())
    return driving_score


@pytest.mark.asyncio
async def test_driving_score(
    driving_score: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.single_trips(). Needs more work."""
    for driving_score_input in driving_score:
        driving_score_json = json.loads(driving_score_input)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/vehicle-status/{target_vin}/driving-score",
            body=driving_score_input,
        )
        driving_score_result = await myskoda.get_driving_score(target_vin)

        calc_date = driving_score_result.last_calculation_date
        assert calc_date is not None
        assert calc_date.isoformat() == driving_score_json["lastCalculationDate"]

        daily_score = driving_score_result.daily_score
        daily_score_json = driving_score_json["dailyScore"]
        assert_driving_score_result(daily_score, daily_score_json)

        weekly_score = driving_score_result.weekly_score
        weekly_score_json = driving_score_json["weeklyScore"]
        assert_driving_score_result(weekly_score, weekly_score_json)

        monthly_score = driving_score_result.monthly_score
        monthly_score_json = driving_score_json["monthlyScore"]
        assert_driving_score_result(monthly_score, monthly_score_json)

        quarterly_score = driving_score_result.quarterly_score
        quarterly_score_json = driving_score_json["quarterlyScore"]
        assert_driving_score_result(quarterly_score, quarterly_score_json)


def assert_driving_score_result(
    driving_score_result: DrivingScoreResult | None, driving_score_json: dict
) -> None:
    assert driving_score_result is not None
    assert driving_score_result.main == driving_score_json["main"]
    assert driving_score_result.braking == driving_score_json["braking"]
    assert driving_score_result.in_flow == driving_score_json["inFlow"]
    assert driving_score_result.acceleration == driving_score_json["acceleration"]
    assert driving_score_result.energy_level == driving_score_json["energyLevel"]
    assert driving_score_result.favorable_conditions == driving_score_json["favorableConditions"]
    assert driving_score_result.excessive_trip == driving_score_json["excessiveTrip"]
    assert driving_score_result.average_consumption == driving_score_json["averageConsumption"]
    assert driving_score_result.main_bonus == driving_score_json["mainBonus"]
    assert driving_score_result.mastered == driving_score_json["mastered"]


@pytest.fixture(name="vehicle_information")
def load_vehicle_information() -> list[str]:
    """Load vehicle information fixture."""
    vehicle_information = []
    for path in [
        "superb/vehicle-info-iV.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            vehicle_information.append(file.read())
    return vehicle_information


@pytest.mark.asyncio
async def test_vehicle_info(
    vehicle_information: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.vehicle_info(). Needs more work."""
    for vehicle_information_input in vehicle_information:
        vehicle_information_json = json.loads(vehicle_information_input)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v1/vehicle-information/{target_vin}",
            body=vehicle_information_input,
        )
        get_vehicle_info_result = await myskoda.get_vehicle_info(target_vin)

        # Add assertions for vehicle info result
        assert get_vehicle_info_result.device_platform == vehicle_information_json["devicePlatform"]
        assert get_vehicle_info_result.renders == vehicle_information_json["renders"]
        vehicle_specification = get_vehicle_info_result.vehicle_specification
        vehicle_specification_json = vehicle_information_json["vehicleSpecification"]
        assert vehicle_specification.title == vehicle_specification_json["title"]
        assert vehicle_specification.manufacturing_date == date.fromisoformat(
            vehicle_specification_json["manufacturingDate"]
        )
        assert vehicle_specification.model == vehicle_specification_json["model"]
        assert vehicle_specification.model_year == vehicle_specification_json["modelYear"]
        assert vehicle_specification.body == vehicle_specification_json["body"]
        assert vehicle_specification.trim_level == vehicle_specification_json["trimLevel"]
        assert vehicle_specification.system_code == vehicle_specification_json["systemCode"]
        assert vehicle_specification.system_model_id == vehicle_specification_json["systemModelId"]
        engine = vehicle_specification.engine
        engine_json = vehicle_specification_json["engine"]
        assert engine.capacity_in_liters == engine_json["capacityInLiters"]
        assert engine.type == engine_json["type"]
        assert engine.power == engine_json["powerInKW"]
        gearbox = vehicle_specification.gearbox
        gearbox_json = vehicle_specification_json["gearbox"]
        assert gearbox is not None
        assert gearbox.type == gearbox_json["type"]

        composite_renders = get_vehicle_info_result.composite_renders
        composite_renders_json = vehicle_information_json["compositeRenders"]
        assert len(composite_renders) == len(composite_renders_json)
        for i in range(len(composite_renders)):
            assert composite_renders[i].view_type == composite_renders_json[i]["viewType"]
            layers = composite_renders[i].layers
            layers_json = composite_renders_json[i]["layers"]
            assert len(layers) == len(layers_json)
            for j in range(len(layers)):
                assert layers[j].order == layers_json[j]["order"]
                assert layers[j].type == layers_json[j]["type"]
                assert layers[j].url == layers_json[j]["url"]
                assert layers[j].view_point == layers_json[j]["viewPoint"]


@pytest.fixture(name="vehicle_equipment")
def load_vehicle_equipment() -> list[str]:
    """Load vehicle equipment fixture."""
    vehicle_equipment = []
    for path in [
        "superb/vehicle-equipment-iV.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            vehicle_equipment.append(file.read())
    return vehicle_equipment


@pytest.mark.asyncio
async def test_vehicle_equipment(
    vehicle_equipment: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.vehicle_info(). Needs more work."""
    for vehicle_equipment_input in vehicle_equipment:
        vehicle_equipment_json = json.loads(vehicle_equipment_input)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v1/vehicle-information/{target_vin}/equipment",
            body=vehicle_equipment_input,
        )
        get_vehicle_equipment_result = (await myskoda.get_vehicle_equipment(target_vin)).equipment
        get_vehicle_equipment_result_json = vehicle_equipment_json["equipment"]

        # Add assertions for vehicle equipment result

        assert len(get_vehicle_equipment_result) == len(get_vehicle_equipment_result_json)
        for i in range(len(get_vehicle_equipment_result)):
            equipment = get_vehicle_equipment_result[i]
            equipment_json = get_vehicle_equipment_result_json[i]

            assert equipment.name == equipment_json["name"]
            assert equipment.description == equipment_json["description"]
            assert equipment.video_url == equipment_json["videoUrl"]
            assert equipment.video_thumbnail_url == equipment_json["videoThumbnailUrl"]


@pytest.fixture(name="vehicle_renders")
def load_vehicle_renders() -> list[str]:
    """Load vehicle renders fixture."""
    vehicle_renders = []
    for path in [
        "superb/vehicle-renders-iV.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            vehicle_renders.append(file.read())
    return vehicle_renders


@pytest.mark.asyncio
async def test_vehicle_renders(
    vehicle_renders: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.vehicle_info(). Needs more work."""
    for vehicle_renders_input in vehicle_renders:
        vehicle_renders_json = json.loads(vehicle_renders_input)

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v1/vehicle-information/{target_vin}/renders",
            body=vehicle_renders_input,
        )
        get_vehicle_renders_result = (
            await myskoda.get_vehicle_renders(target_vin)
        ).composite_renders
        get_vehicle_renders_result_json = vehicle_renders_json["compositeRenders"]

        # Add assertions for vehicle renders result

        assert len(get_vehicle_renders_result) == len(get_vehicle_renders_result_json)
        for i in range(len(get_vehicle_renders_result)):
            render = get_vehicle_renders_result[i]
            render_json = get_vehicle_renders_result_json[i]

            assert render.view_type == render_json["viewType"]
            for j in range(len(render.layers)):
                layer = render.layers[j]
                layer_json = render_json["layers"][j]
                assert layer.order == layer_json["order"]
                assert layer.type == layer_json["type"]
                assert layer.url == layer_json["url"]
                assert layer.view_point == layer_json["viewPoint"]


BASE_URL = "https://mysmob.api.connect.skoda-auto.cz/api"
HTTP_NOT_FOUND = 404


@pytest.mark.asyncio
async def test_raw_request_get(api: RestApi, responses: aioresponses) -> None:
    """raw_request GET returns the response body as a string."""
    body = '{"key": "value"}'
    responses.get(url=f"{BASE_URL}/v1/some/path", body=body)

    result = await api.raw_request(url="/v1/some/path", method="GET")

    assert result == body


@pytest.mark.asyncio
async def test_raw_request_post_with_body(api: RestApi, responses: aioresponses) -> None:
    """raw_request POST sends JSON body and returns the response body."""
    response_body = '{"status": "ok"}'
    responses.post(url=f"{BASE_URL}/v1/some/path", body=response_body)

    result = await api.raw_request(url="/v1/some/path", method="POST", json={"chargingCurrent": 20})

    assert result == response_body


@pytest.mark.asyncio
async def test_raw_request_empty_response(api: RestApi, responses: aioresponses) -> None:
    """raw_request returns an empty string when the response body is empty."""
    responses.post(url=f"{BASE_URL}/v1/some/path", body="")

    result = await api.raw_request(url="/v1/some/path", method="POST")

    assert result == ""


@pytest.mark.asyncio
async def test_raw_request_http_error(api: RestApi, responses: aioresponses) -> None:
    """raw_request raises ClientResponseError on HTTP error responses."""
    responses.get(url=f"{BASE_URL}/v1/some/path", status=HTTP_NOT_FOUND)

    with pytest.raises(ClientResponseError) as exc_info:
        await api.raw_request(url="/v1/some/path", method="GET")

    assert exc_info.value.status == HTTP_NOT_FOUND


@pytest.fixture(name="widgets")
def load_widgets() -> list[tuple[ParkingPositionState, bool, str]]:
    """Load vehicle widgets fixture."""
    widgets = []
    for path in [
        (ParkingPositionState.PARKED, False, "other/widget-parked.json"),
        (ParkingPositionState.IN_MOTION, False, "other/widget-inmotion.json"),
        (ParkingPositionState.PARKED, True, "other/widget-parked.json"),
        (ParkingPositionState.IN_MOTION, True, "other/widget-inmotion.json"),
    ]:
        with FIXTURES_DIR.joinpath(path[2]).open() as file:
            widgets.append((path[0], path[1], file.read()))
    return widgets


@pytest.mark.asyncio
async def test_widgets(
    widgets: list[tuple[ParkingPositionState, bool, str]], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.widgets(). Needs more work."""
    for widgets_input in widgets:
        widgets_json = json.loads(widgets_input[2])
        parking_position_state = widgets_input[0]
        anonymized = widgets_input[1]

        target_vin = "TMBJM0CKV1N12345"
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/widgets/vehicle-status/{target_vin}",
            body=widgets_input[2],
        )
        get_widgets_result = await myskoda.get_widget(target_vin, anonymize=anonymized)

        # Add assertions for widget result

        assert get_widgets_result is not None
        assert get_widgets_result.vehicle is not None
        if anonymized:
            assert get_widgets_result.vehicle.license_plate == LICENSE_PLATE
            assert get_widgets_result.vehicle.name == VEHICLE_NAME
            assert "W211" not in get_widgets_result.vehicle.render_url
        else:
            assert get_widgets_result.vehicle.name == widgets_json["vehicle"]["name"]
            assert (
                get_widgets_result.vehicle.license_plate == widgets_json["vehicle"]["licensePlate"]
            )
            assert get_widgets_result.vehicle.render_url == widgets_json["vehicle"]["renderUrl"]

        assert get_widgets_result.vehicle_status is not None
        if parking_position_state == ParkingPositionState.PARKED:
            assert (
                get_widgets_result.vehicle_status.doors_locked
                == widgets_json["vehicleStatus"]["doorsLocked"]
            )
        else:
            assert get_widgets_result.vehicle_status.doors_locked is None

        assert (
            get_widgets_result.vehicle_status.driving_range_in_km
            == widgets_json["vehicleStatus"]["drivingRangeInKm"]
        )
        assert get_widgets_result.parking_position is not None
        assert get_widgets_result.parking_position.state == widgets_json["parkingPosition"]["state"]
        if parking_position_state == ParkingPositionState.PARKED:
            assert isinstance(get_widgets_result.parking_position, ParkingPositionParked)
            parking_position: ParkingPositionParked = get_widgets_result.parking_position
            if anonymized:
                assert "50.123456" not in parking_position.maps.light_map_url
                assert "20.123456" not in parking_position.maps.light_map_url
                assert parking_position.gps_coordinates.latitude == LOCATION["latitude"]
                assert parking_position.gps_coordinates.longitude == LOCATION["longitude"]
                assert parking_position.formatted_address == FORMATTED_ADDRESS
            else:
                assert (
                    parking_position.maps.light_map_url
                    == widgets_json["parkingPosition"]["maps"]["lightMapUrl"]
                )
                assert (
                    get_widgets_result.parking_position.gps_coordinates.latitude
                    == widgets_json["parkingPosition"]["gpsCoordinates"]["latitude"]
                )
                assert (
                    get_widgets_result.parking_position.gps_coordinates.longitude
                    == widgets_json["parkingPosition"]["gpsCoordinates"]["longitude"]
                )
                assert (
                    get_widgets_result.parking_position.formatted_address
                    == widgets_json["parkingPosition"]["formattedAddress"]
                )
            assert get_widgets_result.charging_status is not None
            assert (
                get_widgets_result.charging_status.remaining_time_to_fully_charged_in_minutes
                == widgets_json["chargingStatus"]["remainingTimeToFullyChargedInMinutes"]
            )
            assert (
                get_widgets_result.charging_status.state_of_charge_in_percent
                == widgets_json["chargingStatus"]["stateOfChargeInPercent"]
            )
        else:
            assert isinstance(get_widgets_result.parking_position, ParkingPositionInMotion)


@pytest.mark.asyncio
async def test_register_fcm_token_sends_expected_request(
    api: RestApi, responses: aioresponses
) -> None:
    responses.put(
        "https://mysmob.api.connect.skoda-auto.cz/api/v1/notifications-subscriptions/fcm-token"
    )

    await api.register_fcm_token(fcm_token="fcm-token")  # noqa: S106

    [(request_call,)] = responses.requests.values()
    assert request_call.kwargs["json"] == {
        "devicePlatform": "ANDROID",
        "appVersion": "8.11.0",
        "language": "en",
    }
