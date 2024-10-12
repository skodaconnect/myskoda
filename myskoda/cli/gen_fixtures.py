"""Generate a set of test fixtures from your garage."""

from pathlib import Path

import asyncclick as click
from asyncclick.core import Context

from myskoda.models.fixtures import Endpoint
from myskoda.myskoda import MySkoda

FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "gen"


@click.group()
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
    myskoda: MySkoda = ctx.obj["myskoda"]

    ctx.obj["vins"] = await get_vin_list(myskoda, vehicle)
    ctx.obj["name"] = name
    ctx.obj["description"] = description


@gen_fixtures.command()
@click.argument("endpoint", type=click.Choice(Endpoint))  # pyright: ignore [reportArgumentType]
@click.pass_context
async def get(ctx: Context, endpoint: Endpoint) -> None:
    myskoda: MySkoda = ctx.obj["myskoda"]

    fixture = await myskoda.generate_get_fixture(
        name=ctx.obj["name"],
        description=ctx.obj["description"],
        vins=ctx.obj["vins"],
        endpoint=endpoint,
    )

    ctx.obj["print"](fixture.to_dict())


async def get_vin_list(myskoda: MySkoda, vehicle: str) -> list[str]:
    if vehicle != "all":
        return [vehicle]
    return await myskoda.list_vehicle_vins()
