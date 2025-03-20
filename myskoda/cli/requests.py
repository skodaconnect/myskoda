"""Commands dealing with reading data from the Rest API."""

from typing import TYPE_CHECKING

import asyncclick as click
from asyncclick.core import Context

from myskoda.cli.utils import handle_request

if TYPE_CHECKING:
    from myskoda.myskoda import MySkoda


@click.command()
@click.pass_context
async def list_vehicles(ctx: Context) -> None:
    """Print a list of all vehicle identification numbers associated with the account."""
    await handle_request(ctx, ctx.obj["myskoda"].list_vehicle_vins)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def info(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print info for the specified vin."""
    await handle_request(ctx, ctx.obj["myskoda"].get_info, vin, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def status(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print current status for the specified vin."""
    await handle_request(ctx, ctx.obj["myskoda"].get_status, vin, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def air_conditioning(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print current status about air conditioning."""
    await handle_request(ctx, ctx.obj["myskoda"].get_air_conditioning, vin, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def auxiliary_heating(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print current status about auxiliary heating."""
    await handle_request(ctx, ctx.obj["myskoda"].get_auxiliary_heating, vin, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def positions(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print the vehicle's current position."""
    await handle_request(ctx, ctx.obj["myskoda"].get_positions, vin, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def health(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print the vehicle's mileage."""
    await handle_request(ctx, ctx.obj["myskoda"].get_health, vin, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def charging(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print the vehicle's current charging state."""
    await handle_request(ctx, ctx.obj["myskoda"].get_charging, vin, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def charging_profiles(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print the vehicle's charging profiles."""
    await handle_request(ctx, ctx.obj["myskoda"].get_charging_profiles, vin, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def maintenance(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print the vehicle's maintenance information."""
    await handle_request(ctx, ctx.obj["myskoda"].get_maintenance, vin, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def driving_range(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print the vehicle's estimated driving range information."""
    await handle_request(ctx, ctx.obj["myskoda"].get_driving_range, vin, anonymize)


@click.command()
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def user(ctx: Context, anonymize: bool) -> None:
    """Print information about currently logged in user."""
    await handle_request(ctx, ctx.obj["myskoda"].get_user, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def trip_statistics(ctx: Context, vin: str, anonymize: bool) -> None:
    """Print the last trip statics."""
    await handle_request(ctx, ctx.obj["myskoda"].get_trip_statistics, vin, anonymize)


@click.command()
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def garage(ctx: Context, anonymize: bool) -> None:
    """Print garage information (list of vehicles with limited information)."""
    await handle_request(ctx, ctx.obj["myskoda"].rest_api.get_garage, anonymize)


@click.command()
@click.option("spin", "--spin", type=str, required=True)
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def verify_spin(ctx: Context, spin: str, anonymize: bool) -> None:
    """Verify S-PIN."""
    await handle_request(ctx, ctx.obj["myskoda"].verify_spin, spin, anonymize)


@click.command()
@click.argument("vin")
@click.option("anonymize", "--anonymize", help="Strip all personal data.", is_flag=True)
@click.pass_context
async def departure_timers(ctx: Context, vin: str, anonymize: bool) -> None:
    """Get all departure timers."""
    await handle_request(ctx, ctx.obj["myskoda"].get_departure_timers, vin, anonymize)


@click.command()
@click.pass_context
async def auth(ctx: Context) -> None:
    """Extract the auth token."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    print(await myskoda.get_auth_token())
