"""Generate a set of test fixtures from your garage."""

import json
from logging import DEBUG
from pathlib import Path
from typing import Any

import asyncclick as click
import coloredlogs
import yaml
from aiohttp import ClientSession
from aioresponses import aioresponses

from myskoda.const import BASE_URL_SKODA
from myskoda.models.garage import GarageEntry
from myskoda.models.info import CapabilityId
from myskoda.myskoda import TRACE_CONFIG, MySkoda

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "gen"

VIN = "TMOCKAA0AA000000"


def anonymize_info(data: dict) -> dict:
    data["vin"] = VIN
    data["servicePartner"]["servicePartnerId"] = "DEU11111"
    return data


def anonymize_vehicle(data: dict) -> dict:
    data["vin"] = VIN
    return data


def anonymize_maintenance(data: dict) -> dict:
    data["preferredServicePartner"]["name"] = "Mock Service Partner"
    data["preferredServicePartner"]["partnerNumber"] = "11111"
    data["preferredServicePartner"]["id"] = "DEU11111"
    data["preferredServicePartner"]["contact"]["phone"] = "+49 1234 567890"
    data["preferredServicePartner"]["contact"]["url"] = "https://example.com"
    data["preferredServicePartner"]["contact"]["email"] = "service@example.com"
    data["preferredServicePartner"]["address"]["street"] = "Example Street 1"
    data["preferredServicePartner"]["address"]["zipCode"] = "12345"
    data["preferredServicePartner"]["address"]["city"] = "Example Town"
    data["preferredServicePartner"]["location"]["latitude"] = 53.400000
    data["preferredServicePartner"]["location"]["longitude"] = 9.700000
    data["predictiveMaintenance"]["setting"]["email"] = "user@example.com"
    data["predictiveMaintenance"]["setting"]["phone"] = "+49 0987 654321"

    return data


def anonymize_charging(data: dict) -> dict:
    return data


def anonymize_status(data: dict) -> dict:
    return data


def anonymize_air_conditioning(data: dict) -> dict:
    return data


def anonymize_positions(data: dict) -> dict:
    for position in data["positions"]:
        position["gpsCoordinates"]["latitude"] = 53.400000
        position["gpsCoordinates"]["longitude"] = 9.700000
        position["address"]["city"] = "Example City"
        position["address"]["street"] = "Example Avenue"
        position["address"]["houseNumber"] = "15"
        position["address"]["zipCode"] = "54321"
    return data


def anonymize_driving_range(data: dict) -> dict:
    return data


def anonymize_trip_statistics(data: dict) -> dict:
    return data


def anonymize_health(data: dict) -> dict:
    return data


@click.command()
@click.option("username", "--user", help="Username used for login.", required=True)
@click.option("password", "--password", help="Password used for login.", required=True)
@click.option("vin", "--vin", help="Generate fixtures for this vin only.")
@click.option("name", "--name", help="Short name describing the vehicle's state.", required=True)
@click.option("description", "--description", help="A longer description.", required=True)
async def cli(username: str, password: str, vin: str | None, name: str, description: str) -> None:
    """Interact with the MySkoda API."""
    coloredlogs.install(level=DEBUG)

    session = ClientSession(trace_configs=[TRACE_CONFIG])
    myskoda = MySkoda(session, mqtt_enabled=False)
    await myskoda.connect(username, password)

    garage = await myskoda.get_garage()

    if garage.vehicles is None:
        await session.close()
        return

    for vehicle in garage.vehicles:
        if vin is not None and vin != vehicle.vin:
            continue

        title = f"{vehicle.title.replace("\u0160koda", "").strip()} {vehicle.system_model_id}"
        path = FIXTURES_DIR.joinpath(title.lower()).joinpath(name.lower())
        path.mkdir(parents=True, exist_ok=True)

        (path / "meta.yaml").write_text(
            yaml.dump(
                {
                    "name": name,
                    "description": description,
                    "vehicle": anonymize_vehicle(vehicle.to_dict()),
                }
            ),
        )

        await generate_fixtures(vehicle, myskoda, path)

    await session.close()


async def generate_fixture(url: str, raw: dict, data: Any, path: Path, vin: str) -> None:  # noqa: ANN401
    with aioresponses() as mocked_responses:
        raw_text = json.dumps(raw)
        mocked_responses.get(url=f"{BASE_URL_SKODA}/api{url}", body=raw_text)
        result = await data

        path.mkdir(parents=True, exist_ok=True)
        (path / "request.yaml").write_text(yaml.dump({"url": url.replace(vin, VIN)}))
        (path / "parsed.yaml").write_text(yaml.dump(result.to_dict()))
        (path / "raw.json").write_text(raw_text)


async def generate_fixtures(vehicle: GarageEntry, myskoda: MySkoda, path: Path) -> None:
    info = await myskoda.rest_api.get_info(vehicle.vin)
    await generate_fixture(
        url=myskoda.rest_api.get_info_url(vehicle.vin),
        raw=anonymize_info(json.loads(await myskoda.rest_api.get_info_raw(vehicle.vin))),
        data=myskoda.rest_api.get_info(vehicle.vin),
        path=path / "info",
        vin=vehicle.vin,
    )
    await generate_fixture(
        url=myskoda.rest_api.get_maintenance_url(vehicle.vin),
        raw=anonymize_maintenance(
            json.loads(await myskoda.rest_api.get_maintenance_raw(vehicle.vin))
        ),
        data=myskoda.rest_api.get_maintenance(vehicle.vin),
        path=path / "maintenance",
        vin=vehicle.vin,
    )
    if info.is_capability_available(CapabilityId.CHARGING):
        await generate_fixture(
            url=myskoda.rest_api.get_charging_url(vehicle.vin),
            raw=anonymize_charging(
                json.loads(await myskoda.rest_api.get_charging_raw(vehicle.vin))
            ),
            data=myskoda.rest_api.get_charging(vehicle.vin),
            path=path / "charging",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.STATE):
        await generate_fixture(
            url=myskoda.rest_api.get_status_url(vehicle.vin),
            raw=anonymize_status(json.loads(await myskoda.rest_api.get_status_raw(vehicle.vin))),
            data=myskoda.rest_api.get_status(vehicle.vin),
            path=path / "status",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.AIR_CONDITIONING):
        await generate_fixture(
            url=myskoda.rest_api.get_air_conditioning_url(vehicle.vin),
            raw=anonymize_air_conditioning(
                json.loads(await myskoda.rest_api.get_air_conditioning_raw(vehicle.vin))
            ),
            data=myskoda.rest_api.get_air_conditioning(vehicle.vin),
            path=path / "air_conditioning",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.PARKING_POSITION):
        await generate_fixture(
            url=myskoda.rest_api.get_positions_url(vehicle.vin),
            raw=anonymize_positions(
                json.loads(await myskoda.rest_api.get_positions_raw(vehicle.vin))
            ),
            data=myskoda.rest_api.get_positions(vehicle.vin),
            path=path / "positions",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.STATE):
        await generate_fixture(
            url=myskoda.rest_api.get_driving_range_url(vehicle.vin),
            raw=anonymize_driving_range(
                json.loads(await myskoda.rest_api.get_driving_range_raw(vehicle.vin))
            ),
            data=myskoda.rest_api.get_driving_range(vehicle.vin),
            path=path / "driving_range",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.TRIP_STATISTICS):
        await generate_fixture(
            url=myskoda.rest_api.get_trip_statistics_url(vehicle.vin),
            raw=anonymize_trip_statistics(
                json.loads(await myskoda.rest_api.get_trip_statistics_raw(vehicle.vin))
            ),
            data=myskoda.rest_api.get_trip_statistics(vehicle.vin),
            path=path / "trip_statistics",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.VEHICLE_HEALTH_INSPECTION):
        await generate_fixture(
            url=myskoda.rest_api.get_health_url(vehicle.vin),
            raw=anonymize_health(json.loads(await myskoda.rest_api.get_health_raw(vehicle.vin))),
            data=myskoda.rest_api.get_health(vehicle.vin),
            path=path / "health",
            vin=vehicle.vin,
        )


if __name__ == "__main__":
    cli()
