"""Generate a set of test fixtures from your garage."""

from pathlib import Path

import asyncclick as click
from asyncclick.core import Context

from myskoda.models.fixtures import create_fixture_vehicle
from myskoda.myskoda import MySkoda

FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "gen"


@click.command()
@click.option(
    "vehicle",
    "--vehicle",
    help="Generate fixtures for this vehicle only (vin). Set to 'all' for all vehicles.",
    required=True,
)
@click.option("name", "--name", help="Short name describing the vehicle's state.", required=True)
@click.option("description", "--description", help="A longer description.")
@click.pass_context
async def gen_fixtures(ctx: Context, vehicle: str, name: str, description: str) -> None:
    """Interact with the MySkoda API."""
    ctx.obj["name"] = name
    ctx.obj["description"] = description

    myskoda: MySkoda = ctx.obj["myskoda"]

    vins = await get_vin_list(myskoda, vehicle)
    vehicles = [create_fixture_vehicle(i, await myskoda.get_info(vin)) for i, vin in enumerate(vins)]
    ctx.obj["vehicles"] = vehicles

    print(vehicles)


async def get_vin_list(myskoda: MySkoda, vehicle: str) -> list[str]:
    if vehicle != "all":
        return [vehicle]
    return await myskoda.list_vehicle_vins()
