"""CLI to test all API functions and models.

Execute with:
poetry run python3 -m myskoda.cli
"""

import asyncio
from collections.abc import Awaitable, Callable
from functools import update_wrapper
from logging import DEBUG, INFO
from typing import ParamSpec, TypeVar

import asyncclick as click
import coloredlogs
from aiohttp import ClientSession
from asyncclick.core import Context
from termcolor import colored

from .event import Event, EventType, ServiceEventTopic
from .models.air_conditioning import AirConditioningState
from .models.charging import MaxChargeCurrent
from .models.common import (
    ActiveState,
    ChargerLockedState,
    ConnectionState,
    DoorLockedState,
    OnOffState,
    OpenState,
)
from .models.operation_request import OperationName, OperationStatus
from .myskoda import TRACE_CONFIG, MySkoda

R = TypeVar("R")
P = ParamSpec("P")


def mqtt_required(func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[Awaitable[R]]]:
    """Enable MQTT before connecting to MySkoda."""

    @click.pass_context
    async def new_func(ctx: Context, *args, **kwargs) -> Awaitable[R]:  # noqa: ANN002, ANN003
        ctx.obj["myskoda"].enable_mqtt = True
        return await ctx.invoke(func, *args, **kwargs)

    return update_wrapper(new_func, func)


async def ensure_connected(ctx: Context) -> None:
    """Ensure that MySkoda is connected, enabling MQTT if necessary."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    username: str = ctx.obj["username"]
    password: str = ctx.obj["password"]
    await myskoda.connect(username, password)


@click.group()
@click.version_option()
@click.option("username", "--user", help="Username used for login.", required=True)
@click.option("password", "--password", help="Password used for login.", required=True)
@click.option("verbose", "--verbose", help="Enable verbose logging.", is_flag=True)
@click.pass_context
async def cli(ctx: Context, username: str, password: str, verbose: bool) -> None:
    """Interact with the MySkoda API."""
    coloredlogs.install(level=DEBUG if verbose else INFO)
    ctx.ensure_object(dict)
    ctx.obj["username"] = username
    ctx.obj["password"] = password

    trace_configs = []
    if verbose:
        trace_configs.append(TRACE_CONFIG)
    session = ClientSession(trace_configs=trace_configs)
    myskoda = MySkoda(session, enable_mqtt=False)

    ctx.obj["myskoda"] = myskoda
    ctx.obj["session"] = session


@cli.result_callback()
@click.pass_context
async def disconnect(
    ctx: Context,
    result: None,  # noqa: ARG001
    username: str,  # noqa: ARG001
    password: str,  # noqa: ARG001
    verbose: bool,  # noqa: ARG001
) -> None:
    myskoda: MySkoda = ctx.obj["myskoda"]
    session: ClientSession = ctx.obj["session"]

    myskoda.disconnect()
    await session.close()


@cli.command()
@click.pass_context
async def auth(ctx: Context) -> None:
    """Extract the auth token."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    print(myskoda.get_auth_token())


@cli.command()
@click.pass_context
async def list_vehicles(ctx: Context) -> None:
    """Print a list of all vehicle identification numbers associated with the account."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]

    print(f"{colored("vehicles:", "blue")}")
    for vehicle in await myskoda.list_vehicle_vins():
        print(f"- {vehicle}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def info(ctx: Context, vin: str) -> None:
    """Print info for the specified vin."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    info = await myskoda.get_info(vin)

    if info.specification.battery is not None:
        print(f"{colored("battery capacity:", "blue")} {info.specification.battery.capacity}kwh")
    print(f"{colored("power:", "blue")} {info.specification.engine.power}kw")
    print(f"{colored("engine:", "blue")} {info.specification.engine.type}")
    print(f"{colored("model:", "blue")} {info.specification.model}")
    print(f"{colored("model id:", "blue")} {info.specification.system_model_id}")
    print(f"{colored("model year:", "blue")} {info.specification.model_year}")
    print(f"{colored("title:", "blue")} {info.specification.title}")
    print(f"{colored("vin:", "blue")} {info.vin}")
    print(f"{colored("software:", "blue")} {info.software_version}")
    print(f"{colored("capabilities:", "blue")}")
    for capability in info.capabilities.capabilities:
        print(f"- {capability.id}")
        if len(capability.statuses) != 0:
            print("  status:")
            for status in capability.statuses:
                print(f"  - {status}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def status(ctx: Context, vin: str) -> None:
    """Print current status for the specified vin."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    status = await myskoda.get_status(vin)

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
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    ac = await myskoda.get_air_conditioning(vin)

    print(f"{colored("window heating:", "blue")} {bool_state(ac.window_heating_enabled)}")
    print(f"{colored("window heating (front):", "blue")} {on(ac.window_heating_state.front)}")
    print(f"{colored("window heating (back):", "blue")} {on(ac.window_heating_state.rear)}")
    if ac.target_temperature is not None:
        print(
            f"{colored("target temperature:", "blue")} "
            f"{ac.target_temperature.temperature_value}°C"
        )
    print(f"{colored("steering wheel position:", "blue")} {ac.steering_wheel_position}")
    print(f"{colored("air conditioning:", "blue")} {ac_on(ac.state)}")
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
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    positions = await myskoda.get_positions(vin)

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
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    health = await myskoda.get_health(vin)

    print(f"{colored("mileage:", "blue")} {health.mileage_in_km}km")
    print(f"{colored("last updated:", "blue")} {health.captured_at}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def charging(ctx: Context, vin: str) -> None:
    """Print the vehicle's current charging state."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    charging = await myskoda.get_charging(vin)

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
    print(f"{colored("target:", "blue")} {charging.settings.target_state_of_charge_in_percent}%")
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
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    maintenance = await myskoda.get_maintenance(vin)

    if maintenance.maintenance_report:
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
    if maintenance.preferred_service_partner:
        print(f"{colored("service partner:", "blue")} {maintenance.preferred_service_partner.name}")
        address = maintenance.preferred_service_partner.address
        print(f"     {address.street} {address.house_number}")
        print(f"     {address.zip_code} {address.city}")
        print(f"     {address.country} ({address.country_code})")
    if maintenance.predictive_maintenance:
        print(f"{colored("email:", "blue")} {maintenance.predictive_maintenance.setting.email}")
        print(
            f"{colored("phone:", "blue")} {maintenance.predictive_maintenance.setting.phone or '-'}"
        )


@cli.command()
@click.argument("vin")
@click.pass_context
async def driving_range(ctx: Context, vin: str) -> None:
    """Print the vehicle's estimated driving range information."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    driving_range = await myskoda.get_driving_range(vin)

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
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    user = await myskoda.get_user()

    print(f"{colored("id:", "blue")} {user.id}")
    print(f"{colored("name:", "blue")} {user.first_name} {user.last_name}")
    print(f"{colored("email:", "blue")} {user.email}")


@cli.command()
@click.argument("vin")
@click.pass_context
async def trip_statistics(ctx: Context, vin: str) -> None:
    """Print the last trip statics."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    stats = await myskoda.get_trip_statistics(vin)

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
@click.argument("operation", type=click.Choice(OperationName))  # pyright: ignore [reportArgumentType]
@mqtt_required
@click.pass_context
async def wait_for_operation(ctx: Context, operation: OperationName) -> None:
    """Wait for the operation with the specified name to complete."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]

    print(f"Waiting for an operation {colored(operation,"green")} to start and complete...")

    await myskoda.mqtt.wait_for_operation(operation)
    print("Completed.")


@cli.command()
@mqtt_required
@click.pass_context
async def subscribe(ctx: Context) -> None:
    """Connect to the MQTT broker and listen for messages."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]

    def on_event(event: Event) -> None:
        print(f"{colored("- type:", "blue")} {event.type}")
        print(f"{colored("  vin:", "blue")} {event.vin}")
        if event.type == EventType.OPERATION:
            operation = event.operation
            print(f"  {colored("version:", "blue")} {operation.version}")
            print(f"  {colored("trace id:", "blue")} {operation.trace_id}")
            print(f"  {colored("request id:", "blue")} {operation.request_id}")
            print(f"  {colored("operation:", "blue")} {operation.operation}")
            print(f"  {colored("status:", "blue")} {operation.status}")
            if status == OperationStatus.ERROR:
                print(f"  {colored("error code:", "blue")} {operation.error_code}")
        elif event.type == EventType.SERVICE_EVENT:
            data = event.event.data
            print(f"  {colored("version:", "blue")} {event.event.version}")
            print(f"  {colored("trace id:", "blue")} {event.event.trace_id}")
            print(f"  {colored("timestamp:", "blue")} {event.event.timestamp}")
            print(f"  {colored("producer:", "blue")} {event.event.producer}")
            print(f"  {colored("name:", "blue")} {event.event.name}")
            print(f"  {colored("vin:", "blue")} {data.vin}")
            print(f"  {colored("user id:", "blue")} {data.user_id}")
            if event.topic == ServiceEventTopic.CHARGING:
                data = event.event.data
                print(f"  {colored("mode:", "blue")} {data.mode}")
                print(f"  {colored("state:", "blue")} {data.state}")
                print(f"  {colored("soc:", "blue")} {data.soc}%")
                print(f"  {colored("charged range:", "blue")} {data.charged_range}km")
                print(f"  {colored("time to finish:", "blue")} {data.time_to_finish}min")

    await myskoda.subscribe(on_event)
    print(f"{colored("Listening for Mqtt events:", "blue")}")
    await asyncio.Event().wait()


@cli.command()
@click.option("temperature", "--temperature", type=float, required=True)
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@mqtt_required
@click.pass_context
async def start_air_conditioning(
    ctx: Context,
    temperature: float,
    timeout: float,  # noqa: ASYNC109
    vin: str,
) -> None:
    """Start the air conditioning with the provided target temperature in °C."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.start_air_conditioning(vin, temperature)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@mqtt_required
@click.pass_context
async def stop_air_conditioning(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Stop the air conditioning."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.stop_air_conditioning(vin)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.option("temperature", "--temperature", type=float, required=True)
@mqtt_required
@click.pass_context
async def set_target_temperature(
    ctx: Context,
    timeout: float,  # noqa: ASYNC109
    vin: str,
    temperature: float,
) -> None:
    """Set the air conditioning's target temperature in °C."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.set_target_temperature(vin, temperature)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@mqtt_required
@click.pass_context
async def start_window_heating(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Start heating both the front and rear window."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.start_window_heating(vin)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@mqtt_required
@click.pass_context
async def stop_window_heating(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Stop heating both the front and rear window."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.stop_window_heating(vin)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.option("limit", "--limit", type=float, required=True)
@mqtt_required
@click.pass_context
async def set_charge_limit(ctx: Context, timeout: float, vin: str, limit: int) -> None:  # noqa: ASYNC109
    """Set the maximum charge limit in percent."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.set_charge_limit(vin, limit)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.option("enabled", "--enabled", type=bool, required=True)
@mqtt_required
@click.pass_context
async def set_battery_care_mode(ctx: Context, timeout: float, vin: str, enabled: bool) -> None:  # noqa: ASYNC109
    """Enable or disable the battery care mode."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.set_battery_care_mode(vin, enabled)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.option("enabled", "--enabled", type=bool, required=True)
@mqtt_required
@click.pass_context
async def set_reduced_current_limit(ctx: Context, timeout: float, vin: str, enabled: bool) -> None:  # noqa: ASYNC109
    """Enable reducing the current limit by which the car is charged."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.set_reduced_current_limit(vin, enabled)


@cli.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@mqtt_required
@click.pass_context
async def wakeup(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Wake the vehicle up. Can be called maximum three times a day."""
    await ensure_connected(ctx)
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.wakeup(vin)


def c_open(cond: OpenState) -> str:
    return colored("open", "red") if cond == OpenState.OPEN else colored("closed", "green")


def locked(cond: DoorLockedState) -> str:
    return (
        colored("locked", "green") if cond == DoorLockedState.LOCKED else colored("unlocked", "red")
    )


def on(cond: OnOffState) -> str:
    return colored("on", "green") if cond == OnOffState.ON else colored("off", "red")


def ac_on(cond: AirConditioningState) -> str:
    return (
        colored("on", "green")
        if cond in (AirConditioningState.ON, AirConditioningState.HEATING)
        else colored("off", "red")
    )


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


def bool_state(cond: bool) -> str:
    return colored("true", "green") if cond else colored("false", "red")


def charger_locked(cond: ChargerLockedState) -> str:
    return (
        colored("locked", "green")
        if cond == ChargerLockedState.LOCKED
        else colored("unlocked", "red")
    )


if __name__ == "__main__":
    cli()
