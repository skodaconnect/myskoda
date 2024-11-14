"""Commands for the CLI for operations that can be performed."""

import asyncio
from typing import TYPE_CHECKING

import asyncclick as click
from asyncclick.core import Context

from myskoda.cli.utils import mqtt_required

if TYPE_CHECKING:
    from myskoda import MySkoda


@click.command()
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


@click.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def stop_air_conditioning(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Stop the air conditioning."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.stop_air_conditioning(vin)


@click.command()
@click.option("temperature", "--temperature", type=float, required=True)
@click.option("spin", "--spin", type=str, required=True)
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def start_auxiliary_heating(
    ctx: Context,
    temperature: float,
    spin: str,
    timeout: float,  # noqa: ASYNC109
    vin: str,
) -> None:
    """Start the auxiliary heating with the provided target temperature in °C."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.start_auxiliary_heating(vin, temperature, spin)


@click.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def stop_auxiliary_heating(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Stop the auxiliary heating."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.stop_auxiliary_heating(vin)


@click.command()
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


@click.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def start_window_heating(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Start heating both the front and rear window."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.start_window_heating(vin)


@click.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def stop_window_heating(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Stop heating both the front and rear window."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.stop_window_heating(vin)


@click.command()
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


@click.command()
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


@click.command()
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


@click.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def wakeup(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Wake the vehicle up. Can be called maximum three times a day."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.wakeup(vin)


@click.command()
@click.option("spin", "--spin", type=str, required=True)
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def lock(
    ctx: Context,
    spin: str,
    timeout: float,  # noqa: ASYNC109
    vin: str,
) -> None:
    """Lock the car."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.lock(vin, spin)


@click.command()
@click.option("spin", "--spin", type=str, required=True)
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def unlock(
    ctx: Context,
    spin: str,
    timeout: float,  # noqa: ASYNC109
    vin: str,
) -> None:
    """Unlock the car."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.unlock(vin, spin)


@click.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def honk_flash(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Honk and/or flash."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.honk_flash(vin)


@click.command()
@click.option("timeout", "--timeout", type=float, default=300)
@click.argument("vin")
@click.pass_context
@mqtt_required
async def flash(ctx: Context, timeout: float, vin: str) -> None:  # noqa: ASYNC109
    """Flash."""
    myskoda: MySkoda = ctx.obj["myskoda"]
    async with asyncio.timeout(timeout):
        await myskoda.flash(vin)
