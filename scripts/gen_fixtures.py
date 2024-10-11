"""Generate a set of test fixtures from your garage."""

from logging import DEBUG
from pathlib import Path
from typing import Any

import asyncclick as click
import coloredlogs
from aiohttp import ClientSession
from aioresponses import aioresponses
from anyio import open_file
from yaml import dump

from myskoda.const import BASE_URL_SKODA
from myskoda.models.garage import GarageEntry
from myskoda.models.info import CapabilityId
from myskoda.myskoda import TRACE_CONFIG, MySkoda

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "gen"
VIN = "TMOCKAA0AA000000"


async def write_file_sanitized(path: Path, content: str, vin: str) -> None:
    content = content.replace(vin, VIN)
    async with await open_file(path, "w") as file:
        await file.write(content)


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

        await write_file_sanitized(
            path / "meta.yaml",
            dump(
                {
                    "name": name,
                    "description": description,
                    "vehicle": vehicle.to_dict(),
                }
            ),
            vehicle.vin,
        )

        await generate_fixtures(vehicle, myskoda, path)

    await session.close()


async def generate_fixture(url: str, raw: str, data: Any, path: Path, vin: str) -> None:  # noqa: ANN401
    with aioresponses() as mocked_responses:
        mocked_responses.get(url=f"{BASE_URL_SKODA}/api{url}", body=raw)
        result = await data

        path.mkdir(parents=True, exist_ok=True)
        await write_file_sanitized(path / "request.yaml", dump({"url": url}), vin)
        await write_file_sanitized(path / "parsed.yaml", dump(result.to_dict()), vin)
        await write_file_sanitized(path / "raw.json", raw, vin)


async def generate_fixtures(vehicle: GarageEntry, myskoda: MySkoda, path: Path) -> None:
    info = await myskoda.rest_api.get_info(vehicle.vin)
    await generate_fixture(
        url=myskoda.rest_api.get_info_url(vehicle.vin),
        raw=await myskoda.rest_api.get_info_raw(vehicle.vin),
        data=myskoda.rest_api.get_info(vehicle.vin),
        path=path / "info",
        vin=vehicle.vin,
    )
    await generate_fixture(
        url=myskoda.rest_api.get_maintenance_url(vehicle.vin),
        raw=await myskoda.rest_api.get_maintenance_raw(vehicle.vin),
        data=myskoda.rest_api.get_maintenance(vehicle.vin),
        path=path / "maintenance",
        vin=vehicle.vin,
    )
    if info.is_capability_available(CapabilityId.CHARGING):
        await generate_fixture(
            url=myskoda.rest_api.get_charging_url(vehicle.vin),
            raw=await myskoda.rest_api.get_charging_raw(vehicle.vin),
            data=myskoda.rest_api.get_charging(vehicle.vin),
            path=path / "charging",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.STATE):
        await generate_fixture(
            url=myskoda.rest_api.get_status_url(vehicle.vin),
            raw=await myskoda.rest_api.get_status_raw(vehicle.vin),
            data=myskoda.rest_api.get_status(vehicle.vin),
            path=path / "status",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.AIR_CONDITIONING):
        await generate_fixture(
            url=myskoda.rest_api.get_air_conditioning_url(vehicle.vin),
            raw=await myskoda.rest_api.get_air_conditioning_raw(vehicle.vin),
            data=myskoda.rest_api.get_air_conditioning(vehicle.vin),
            path=path / "air_conditioning",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.PARKING_POSITION):
        await generate_fixture(
            url=myskoda.rest_api.get_positions_url(vehicle.vin),
            raw=await myskoda.rest_api.get_positions_raw(vehicle.vin),
            data=myskoda.rest_api.get_positions(vehicle.vin),
            path=path / "positions",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.STATE):
        await generate_fixture(
            url=myskoda.rest_api.get_driving_range_url(vehicle.vin),
            raw=await myskoda.rest_api.get_driving_range_raw(vehicle.vin),
            data=myskoda.rest_api.get_driving_range(vehicle.vin),
            path=path / "driving_range",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.TRIP_STATISTICS):
        await generate_fixture(
            url=myskoda.rest_api.get_trip_statistics_url(vehicle.vin),
            raw=await myskoda.rest_api.get_trip_statistics_raw(vehicle.vin),
            data=myskoda.rest_api.get_trip_statistics(vehicle.vin),
            path=path / "trip_statistics",
            vin=vehicle.vin,
        )
    if info.is_capability_available(CapabilityId.VEHICLE_HEALTH_INSPECTION):
        await generate_fixture(
            url=myskoda.rest_api.get_health_url(vehicle.vin),
            raw=await myskoda.rest_api.get_health_raw(vehicle.vin),
            data=myskoda.rest_api.get_health(vehicle.vin),
            path=path / "health",
            vin=vehicle.vin,
        )


if __name__ == "__main__":
    cli()
