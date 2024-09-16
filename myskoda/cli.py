"""CLI to test all API functions and models.

Execute with:
poetry run python3 -m myskoda.cli
"""

import asyncclick as click
from aiohttp import ClientSession
from asyncclick.core import Context
from termcolor import colored

from myskoda.mqtt import MQTT

from . import idk_authorize
from .models.charging import MaxChargeCurrent
from .models.common import (
    ActiveState,
    ChargerLockedState,
    ConnectionState,
    DoorLockedState,
    OnOffState,
    OpenState,
)
from .rest_api import RestApi


@click.group()
@click.version_option()
@click.option("username", "--user", help="Username used for login.", required=True)
@click.option("password", "--password", help="Password used for login.", required=True)
@click.pass_context
def cli(ctx: Context, username: str, password: str) -> None:
    """Interact with the MySkoda API."""
    ctx.ensure_object(dict)
    ctx.obj["username"] = username
    ctx.obj["password"] = password


@cli.command()
@click.pass_context
async def auth(ctx: Context) -> None:
    """Extract the auth token."""
    async with ClientSession() as session:
        auth_codes = await idk_authorize(session, ctx.obj["username"], ctx.obj["password"])
        print(auth_codes.access_token)


@cli.command()
@click.pass_context
async def list_vehicles(ctx: Context) -> None:
    """Print a list of all vehicle identification numbers associated with the account."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        print(f"{colored("vehicles:", "blue")}")
        for vehicle in await hub.list_vehicles():
            print(f"- {vehicle}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def info(ctx: Context, vin: str) -> None:
    """Print info for the specified vin."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        info = await hub.get_info(vin)

        if info.specification.battery is not None:
            print(
                f"{colored("battery capacity:", "blue")} {info.specification.battery.capacity}kwh"
            )
        print(f"{colored("power:", "blue")} {info.specification.engine.power}kw")
        print(f"{colored("engine:", "blue")} {info.specification.engine.type}")
        print(f"{colored("model:", "blue")} {info.specification.model}")
        print(f"{colored("model id:", "blue")} {info.specification.system_model_id}")
        print(f"{colored("model year:", "blue")} {info.specification.model_year}")
        print(f"{colored("title:", "blue")} {info.specification.title}")
        print(f"{colored("vin:", "blue")} {info.vin}")
        print(f"{colored("software:", "blue")} {info.software_version}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def status(ctx: Context, vin: str) -> None:
    """Print current status for the specified vin."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        status = await hub.get_status(vin)

        print(
            f"{colored("doors:", "blue")} {c_open(status.overall.doors)}, "
            f"{locked(status.overall.doors_locked)}"
        )
        print(f"{colored("bonnet:", "blue")} {c_open(status.detail.bonnet)}")
        print(f"{colored("trunk:", "blue")} {c_open(status.detail.trunk)}")
        print(f"{colored("windows:", "blue")} {c_open(status.overall.windows)}")
        print(f"{colored("lights:", "blue")} {on(status.overall.lights)}")
        print(f"{colored("last update:", "blue")} {status.car_captured_timestamp}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def air_conditioning(ctx: Context, vin: str) -> None:
    """Print current status about air conditioning."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        ac = await hub.get_air_conditioning(vin)

        print(f"{colored("window heating:", "blue")} {bool_state(ac.window_heating_enabled)}")
        print(f"{colored("window heating (front):", "blue")} {on(ac.window_heating_state.front)}")
        print(f"{colored("window heating (back):", "blue")} {on(ac.window_heating_state.rear)}")
        if ac.target_temperature is not None:
            print(
                f"{colored("target temperature:", "blue")} "
                f"{ac.target_temperature.temperature_value}°C"
            )
        print(f"{colored("steering wheel position:", "blue")} {ac.steering_wheel_position}")
        print(f"{colored("air conditioning:", "blue")} {on(ac.state)}")
        print(f"{colored("state:", "blue")} {ac.state}")
        print(
            f"{colored("charger:", "blue")} {connected(ac.charger_connection_state)}, "
            f"{charger_locked(ac.charger_lock_state)}"
        )
        print(
            f"{colored("temperature reached:", "blue")} "
            f"{ac.estimated_date_time_to_reach_target_temperature}"
        )


@cli.command()
@click.argument("vin")
@click.pass_context
async def positions(ctx: Context, vin: str) -> None:
    """Print the vehicle's current position."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        positions = await hub.get_positions(vin)

        for position in positions.positions:
            print(f"- {colored("type:", "blue")} {position.type}")
            print(f"  {colored("latitude:", "blue")} {position.gps_coordinates.latitude}")
            print(f"  {colored("longitude:", "blue")} {position.gps_coordinates.longitude}")
            print(f"  {colored("address:", "blue")}")
            print(f"     {position.address.street} {position.address.house_number}")
            print(f"     {position.address.zip_code} {position.address.city}")
            print(f"     {position.address.country} ({position.address.country_code})")

        if positions.errors:
            print(f"{colored("Error:", "red")}")
        for error in positions.errors:
            print(f"- {colored("type:", "blue")} {error.type}")
            print(f"  {colored("description:", "blue")} {error.description}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def health(ctx: Context, vin: str) -> None:
    """Print the vehicle's mileage."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        health = await hub.get_health(vin)

        print(f"{colored("mileage:", "blue")} {health.mileage_in_km}km")
        print(f"{colored("last updated:", "blue")} {health.captured_at}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def charging(ctx: Context, vin: str) -> None:
    """Print the vehicle's current charging state."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        charging = await hub.get_charging(vin)

        if charging.status is not None:
            print(
                f"{colored("battery charge:", "blue")} "
                f"{charging.status.battery.state_of_charge_in_percent}%"
            )
            print(
                f"{colored("remaining distance:", "blue")} "
                f"{charging.status.battery.remaining_cruising_range_in_meters / 1000}km"
            )
            print(f"{colored("state:", "blue")} {charging.status.state}")
            print(f"{colored("charger type:", "blue")} {charging.status.charge_type}")
            print(
                f"{colored("charging rate:", "blue")} "
                f"{charging.status.charging_rate_in_kilometers_per_hour}km/h"
            )
            print(
                f"{colored("remaining time:", "blue")} "
                f"{charging.status.remaining_time_to_fully_charged_in_minutes}min"
            )
            print(f"{colored("charging power:", "blue")} {charging.status.charge_power_in_kw}kw")
        print(
            f"{colored("target:", "blue")} {charging.settings.target_state_of_charge_in_percent}%"
        )
        print(
            f"{colored("battery care mode:", "blue")} "
            f"{active(charging.settings.charging_care_mode)}"
        )
        print(
            f"{colored("current:", "blue")} "
            f"{charge_current(charging.settings.max_charge_current_ac)}"
        )


@cli.command()
@click.argument("vin")
@click.pass_context
async def maintenance(ctx: Context, vin: str) -> None:
    """Print the vehicle's maintenance information."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        maintenance = await hub.get_maintenance(vin)

        print(f"{colored("mileage:", "blue")} {maintenance.maintenance_report.mileage_in_km}km")
        print(
            f"{colored("inspection due in:", "blue")} "
            f"{maintenance.maintenance_report.inspection_due_in_days}d / "
            f"{maintenance.maintenance_report.inspection_due_in_km}km"
        )
        print(
            f"{colored("oil service due in:", "blue")} "
            f"{maintenance.maintenance_report.oil_service_due_in_days}d / "
            f"{maintenance.maintenance_report.oil_service_due_in_km}km"
        )
        print(f"{colored("service partner:", "blue")} {maintenance.preferred_service_partner.name}")
        address = maintenance.preferred_service_partner.address
        print(f"     {address.street} {address.house_number}")
        print(f"     {address.zip_code} {address.city}")
        print(f"     {address.country} ({address.country_code})")
        if maintenance.predictive_maintenance:
            print(f"{colored("email:", "blue")} {maintenance.predictive_maintenance.setting.email}")
            print(f"{colored("phone:", "blue")} {maintenance.predictive_maintenance.setting.phone}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def driving_range(ctx: Context, vin: str) -> None:
    """Print the vehicle's estimated driving range information."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        driving_range = await hub.get_driving_range(vin)

        print(f"{colored("range:", "blue")} {driving_range.total_range_in_km}km")
        print(f"{colored("car type:", "blue")} {driving_range.car_type}")
        print(f"{colored("last update:", "blue")} {driving_range.car_captured_timestamp}")
        print(
            f"{colored("fuel level:", "blue")} "
            f"{driving_range.primary_engine_range.current_fuel_level_in_percent}%"
        )


@cli.command()
@click.pass_context
async def user(ctx: Context) -> None:
    """Print information about currently logged in user."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        user = await hub.get_user()

        print(f"{colored("id:", "blue")} {user.id}")
        print(f"{colored("name:", "blue")} {user.first_name} {user.last_name}")
        print(f"{colored("email:", "blue")} {user.email}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def trip_statistics(ctx: Context, vin: str) -> None:
    """Print the last trip statics."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])
        stats = await hub.get_trip_statistics(vin)

        print(
            f"{colored("overall fuel consumption:", "blue")} "
            f"{stats.overall_average_fuel_consumption}l/100km"
        )
        print(f"{colored("mileage:", "blue")} {stats.overall_mileage_in_km}km")
        print(f"{colored("entries:", "blue")}")
        for entry in stats.detailed_statistics:
            print(f"- {colored("date:", "blue")} {entry.date}")
            print(
                f"  {colored("average fuel consumption:", "blue")} "
                f"{entry.average_fuel_consumption}l/100km"
            )
            print(f"  {colored("average speed:", "blue")} {entry.average_speed_in_kmph}km/h")
            print(f"  {colored("mileage:", "blue")} {entry.mileage_in_km}km")


@cli.command()
@click.pass_context
async def mqtt(ctx: Context) -> None:
    """Connect to the MQTT broker and listen for messages."""
    async with ClientSession() as session:
        hub = RestApi(session)
        await hub.authenticate(ctx.obj["username"], ctx.obj["password"])

        mqtt = MQTT(hub)
        await mqtt.connect()
        mqtt.loop_forever()


def c_open(cond: OpenState) -> str:
    return colored("open", "red") if cond == OpenState.OPEN else colored("closed", "green")


def locked(cond: DoorLockedState) -> str:
    return (
        colored("locked", "green") if cond == DoorLockedState.LOCKED else colored("unlocked", "red")
    )


def on(cond: OnOffState) -> str:
    return colored("on", "green") if cond == OnOffState.ON else colored("off", "red")


def connected(cond: ConnectionState) -> str:
    return (
        colored("connected", "green")
        if cond == ConnectionState.CONNECTED
        else colored("disconnected", "red")
    )


def active(cond: ActiveState) -> str:
    return (
        colored("active", "green") if cond == ActiveState.ACTIVATED else colored("inactive", "red")
    )


def charge_current(cond: MaxChargeCurrent) -> str:
    return (
        colored("maximum", "green")
        if cond == MaxChargeCurrent.MAXIMUM
        else colored("reduced", "red")
    )


def bool_state(cond: bool) -> str:  # noqa: FBT001
    return colored("true", "green") if cond else colored("false", "red")


def charger_locked(cond: ChargerLockedState) -> str:
    return (
        colored("locked", "green")
        if cond == ChargerLockedState.LOCKED
        else colored("unlocked", "red")
    )


if __name__ == "__main__":
    cli()
