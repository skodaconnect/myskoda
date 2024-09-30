"""CLI to test all API functions and models.

Execute with:
poetry run python3 -m myskoda.cli
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from enum import StrEnum
from functools import update_wrapper
from logging import DEBUG, INFO

import asyncclick as click
import coloredlogs
import yaml
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError
from asyncclick.core import Context
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer, YamlLexer
from termcolor import colored

from myskoda.event import Event
from myskoda.models.operation_request import OperationName

from .myskoda import TRACE_CONFIG, MqttDisabledError, MySkoda


def mqtt_required[R](func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[Awaitable[R]]]:
    """Enable MQTT before connecting to MySkoda."""

    @click.pass_context
    async def new_func(ctx: Context, *args, **kwargs) -> Awaitable[R]:  # noqa: ANN002, ANN003
        if ctx.obj["mqtt_disabled"]:
            return await ctx.invoke(func, *args, **kwargs)
        myskoda: MySkoda = ctx.obj["myskoda"]
        await myskoda.enable_mqtt()
        return await ctx.invoke(func, *args, **kwargs)

    return update_wrapper(new_func, func)


class Format(StrEnum):
    JSON = "json"
    YAML = "yaml"


@click.group()
@click.version_option()
@click.option("username", "--user", help="Username used for login.", required=True)
@click.option("password", "--password", help="Password used for login.", required=True)
@click.option("verbose", "--verbose", help="Enable verbose logging.", is_flag=True)
@click.option(
    "output_format",
    "--format",
    help="Select the output format. JSON or YAML.",
    type=click.Choice(Format),  # pyright: ignore [reportArgumentType]
    default=Format.YAML,
)
@click.option("trace", "--trace", help="Enable tracing of HTTP requests.", is_flag=True)
@click.option("disable_mqtt", "--disable-mqtt", help="Do not connect to MQTT.", is_flag=True)
@click.pass_context
async def cli(  # noqa: PLR0913
    ctx: Context,
    username: str,
    password: str,
    verbose: bool,
    output_format: Format,
    trace: bool,
    disable_mqtt: bool,
) -> None:
    """Interact with the MySkoda API."""
    coloredlogs.install(level=DEBUG if verbose else INFO)
    ctx.ensure_object(dict)
    ctx.obj["username"] = username
    ctx.obj["password"] = password
    if output_format == Format.JSON:
        ctx.obj["print"] = _print_json
    elif output_format == Format.YAML:
        ctx.obj["print"] = _print_yaml

    ctx.obj["mqtt_disabled"] = disable_mqtt

    trace_configs = []
    if trace:
        trace_configs.append(TRACE_CONFIG)
    session = ClientSession(trace_configs=trace_configs)
    myskoda = MySkoda(session, mqtt_enabled=False)
    await myskoda.connect(username, password)

    ctx.obj["myskoda"] = myskoda
    ctx.obj["session"] = session


def _print_json(data: dict) -> None:
    print(highlight(json.dumps(data, indent=4), JsonLexer(), TerminalFormatter()))


def _print_yaml(data: dict) -> None:
    print(highlight(yaml.dump(data), YamlLexer(), TerminalFormatter()))


@cli.result_callback()
@click.pass_context
async def disconnect(  # noqa: PLR0913
    ctx: Context,
    result: None,  # noqa: ARG001
    username: str,  # noqa: ARG001
    password: str,  # noqa: ARG001
    verbose: bool,  # noqa: ARG001
    output_format: Format,  # noqa: ARG001
    trace: bool,  # noqa: ARG001
    disable_mqtt: bool,  # noqa: ARG001
) -> None:
    myskoda: MySkoda = ctx.obj["myskoda"]
    session: ClientSession = ctx.obj["session"]

    myskoda.disconnect()
    await session.close()


@cli.command()
@click.pass_context
async def auth(ctx: Context) -> None:
    """Extract the auth token."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    print(myskoda.get_auth_token())


@cli.command()
@click.pass_context
async def list_vehicles(ctx: Context) -> None:
    """Print a list of all vehicle identification numbers associated with the account."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    vehicles = await myskoda.list_vehicle_vins()
    ctx.obj["print"](vehicles)


@cli.command()
@click.argument("vin")
@click.pass_context
async def info(ctx: Context, vin: str) -> None:
    """Print info for the specified vin."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    info = await myskoda.get_info(vin)
    ctx.obj["print"](info.to_dict())


@cli.command()
@click.argument("vin")
@click.pass_context
async def status(ctx: Context, vin: str) -> None:
    """Print current status for the specified vin."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    status = await myskoda.get_status(vin)
    ctx.obj["print"](status.to_dict())


@cli.command()
@click.argument("vin")
@click.pass_context
async def air_conditioning(ctx: Context, vin: str) -> None:
    """Print current status about air conditioning."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    ac = await myskoda.get_air_conditioning(vin)
    ctx.obj["print"](ac.to_dict())


@cli.command()
@click.argument("vin")
@click.pass_context
async def positions(ctx: Context, vin: str) -> None:
    """Print the vehicle's current position."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    positions = await myskoda.get_positions(vin)
    ctx.obj["print"](positions.to_dict())


@cli.command()
@click.argument("vin")
@click.pass_context
async def health(ctx: Context, vin: str) -> None:
    """Print the vehicle's mileage."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    health = await myskoda.get_health(vin)
    ctx.obj["print"](health.to_dict())


@cli.command()
@click.argument("vin")
@click.pass_context
async def charging(ctx: Context, vin: str) -> None:
    """Print the vehicle's current charging state."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    charging = await myskoda.get_charging(vin)
    ctx.obj["print"](charging.to_dict())


@cli.command()
@click.argument("vin")
@click.pass_context
async def maintenance(ctx: Context, vin: str) -> None:
    """Print the vehicle's maintenance information."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    maintenance = await myskoda.get_maintenance(vin)
    ctx.obj["print"](maintenance.to_dict())


@cli.command()
@click.argument("vin")
@click.pass_context
async def driving_range(ctx: Context, vin: str) -> None:
    """Print the vehicle's estimated driving range information."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    driving_range = await myskoda.get_driving_range(vin)
    ctx.obj["print"](driving_range.to_dict())


@cli.command()
@click.pass_context
async def user(ctx: Context) -> None:
    """Print information about currently logged in user."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    user = await myskoda.get_user()
    ctx.obj["print"](user.to_dict())


@cli.command()
@click.argument("vin")
@click.pass_context
async def trip_statistics(ctx: Context, vin: str) -> None:
    """Print the last trip statics."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    try:
        stats = await myskoda.get_trip_statistics(vin)
        ctx.obj["print"](stats.to_dict())
    except ClientResponseError as e:
        ctx.obj["print"]({"error": e.status, "message": e.message, "url": str(e.request_info.url)})


@cli.command()
@click.argument("operation", type=click.Choice(OperationName))  # pyright: ignore [reportArgumentType]
@click.pass_context
@mqtt_required
async def wait_for_operation(ctx: Context, operation: OperationName) -> None:
    """Wait for the operation with the specified name to complete."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    if myskoda.mqtt is None:
        raise MqttDisabledError

    print(f"Waiting for an operation {colored(operation,"green")} to start and complete...")

    await myskoda.mqtt.wait_for_operation(operation)
    print("Completed.")


@cli.command()
@click.pass_context
@mqtt_required
async def subscribe(ctx: Context) -> None:
    """Connect to the MQTT broker and listen for messages."""
    myskoda: MySkoda = ctx.obj["myskoda"]

    def on_event(event: Event) -> None:
        ctx.obj["print"](event.to_dict())

    myskoda.subscribe(on_event)
    await asyncio.Event().wait()


@cli.command()
@click.option("temperature", "--temperature", type=float, required=True)
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def start_air_conditioning(
    ctx: Context,
    temperature: float,
    timeout: float,  # noqa: ASYNC109
    vin: str,
) -> None:
    """Start the air conditioning with the provided target temperature in °C."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.start_air_conditioning(vin, temperature)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
async def stop_air_conditioning(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Stop the air conditioning."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.stop_air_conditioning(vin)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.option("temperature", "--temperature", type=float, required=True)
@click.pass_context
@mqtt_required
async def set_target_temperature(
    ctx: Context,
    timeout: float,  # noqa: ASYNC109
    vin: str,
    temperature: float,
) -> None:
    """Set the air conditioning's target temperature in °C."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.set_target_temperature(vin, temperature)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def start_window_heating(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Start heating both the front and rear window."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.start_window_heating(vin)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def stop_window_heating(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Stop heating both the front and rear window."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.stop_window_heating(vin)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.option("limit", "--limit", type=float, required=True)
@click.pass_context
@mqtt_required
async def set_charge_limit(ctx: Context, timeout: float, vin: str, limit: int) -> None:  # noqa: ASYNC109
    """Set the maximum charge limit in percent."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.set_charge_limit(vin, limit)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.option("enabled", "--enabled", type=bool, required=True)
@click.pass_context
@mqtt_required
async def set_battery_care_mode(ctx: Context, timeout: float, vin: str, enabled: bool) -> None:  # noqa: ASYNC109
    """Enable or disable the battery care mode."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.set_battery_care_mode(vin, enabled)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.option("enabled", "--enabled", type=bool, required=True)
@click.pass_context
@mqtt_required
async def set_reduced_current_limit(ctx: Context, timeout: float, vin: str, enabled: bool) -> None:  # noqa: ASYNC109
    """Enable reducing the current limit by which the car is charged."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.set_reduced_current_limit(vin, enabled)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def wakeup(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Wake the vehicle up. Can be called maximum three times a day."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.wakeup(vin)


if __name__ == "__main__":
    cli()
