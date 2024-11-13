"""CLI to test all API functions and models.

Execute with:
poetry run python3 -m myskoda.cli
"""

from logging import DEBUG, INFO
from sys import platform as sys_platform
from sys import version_info as sys_version_info

import asyncclick as click
import coloredlogs
from aiohttp import ClientSession
from asyncclick.core import Context

from myskoda import TRACE_CONFIG, MySkoda
from myskoda.cli.gen_fixtures import gen_fixtures
from myskoda.cli.mqtt import subscribe, wait_for_operation
from myskoda.cli.operations import (
    flash,
    honk_flash,
    lock,
    set_charge_limit,
    set_reduced_current_limit,
    set_target_temperature,
    start_air_conditioning,
    start_auxiliary_heating,
    start_window_heating,
    stop_air_conditioning,
    stop_auxiliary_heating,
    stop_window_heating,
    unlock,
    wakeup,
)
from myskoda.cli.requests import (
    air_conditioning,
    auth,
    charging,
    driving_range,
    garage,
    health,
    info,
    list_vehicles,
    maintenance,
    positions,
    status,
    trip_statistics,
    user,
    verify_spin,
)
from myskoda.cli.utils import Format, print_json, print_yaml

if sys_platform.lower().startswith("win") and sys_version_info >= (3, 8):
    # Check if we're on windows, if so, tune asyncio to work there as well (https://github.com/skodaconnect/myskoda/issues/77)
    import asyncio

    try:
        from asyncio import WindowsSelectorEventLoopPolicy  # type: ignore[unknown-import]
    except ImportError:
        pass  # Can't assign a policy which doesn't exist.
    else:
        if not isinstance(asyncio.get_event_loop_policy(), WindowsSelectorEventLoopPolicy):
            asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())


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
        ctx.obj["print"] = print_json
    elif output_format == Format.YAML:
        ctx.obj["print"] = print_yaml

    ctx.obj["mqtt_disabled"] = disable_mqtt

    trace_configs = []
    if trace:
        trace_configs.append(TRACE_CONFIG)

    session = ClientSession(trace_configs=trace_configs)
    myskoda = MySkoda(session, mqtt_enabled=False)
    await myskoda.connect(username, password)

    ctx.obj["myskoda"] = myskoda
    ctx.obj["session"] = session


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

    await myskoda.disconnect()
    await session.close()


cli.add_command(list_vehicles)
cli.add_command(info)
cli.add_command(status)
cli.add_command(air_conditioning)
cli.add_command(positions)
cli.add_command(health)
cli.add_command(charging)
cli.add_command(maintenance)
cli.add_command(driving_range)
cli.add_command(user)
cli.add_command(trip_statistics)
cli.add_command(garage)
cli.add_command(auth)
cli.add_command(start_air_conditioning)
cli.add_command(stop_air_conditioning)
cli.add_command(start_auxiliary_heating)
cli.add_command(stop_auxiliary_heating)
cli.add_command(set_target_temperature)
cli.add_command(start_window_heating)
cli.add_command(stop_window_heating)
cli.add_command(set_charge_limit)
cli.add_command(set_reduced_current_limit)
cli.add_command(wakeup)
cli.add_command(wait_for_operation)
cli.add_command(subscribe)
cli.add_command(gen_fixtures)
cli.add_command(lock)
cli.add_command(unlock)
cli.add_command(honk_flash)
cli.add_command(flash)
cli.add_command(verify_spin)

if __name__ == "__main__":
    cli()
