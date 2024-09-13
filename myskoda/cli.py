from aiohttp import ClientSession
from termcolor import colored
import asyncclick as click

from myskoda.models.charging import MaxChargeCurrent
from myskoda.models.common import OnOffState
from myskoda.myskoda import MySkodaHub
from . import idk_authorize

username: str
password: str


@click.group()
@click.version_option()
@click.option("u", "--user", help="Username used for login.", required=True)
@click.option("p", "--password", help="Password used for login.", required=True)
def cli(u, p):
    """Interact with the MySkoda API."""
    global username, password
    username = u
    password = p


@cli.command()
async def auth():
    """Extract the auth token."""
    async with ClientSession() as session:
        auth_codes = await idk_authorize(session, username, password)
        print(auth_codes.access_token)


@cli.command()
async def list_vehicles():
    """Print a list of all vehicle identification numbers associated with the account."""
    async with ClientSession() as session:
        hub = MySkodaHub(session)
        await hub.authenticate(username, password)
        for vehicle in await hub.list_vehicles():
            print(vehicle)


@cli.command()
@click.argument("vin")
async def info(vin):
    """Print info for the specified vin."""
    async with ClientSession() as session:
        hub = MySkodaHub(session)
        await hub.authenticate(username, password)
        info = await hub.get_info(vin)

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
async def status(vin):
    """Print current status for the specified vin."""
    async with ClientSession() as session:
        hub = MySkodaHub(session)
        await hub.authenticate(username, password)
        status = await hub.get_status(vin)

        print(
            f"{colored("doors:", "blue")} {open(status.doors_open)}, {locked(status.doors_locked)}"
        )
        print(f"{colored("bonnet:", "blue")} {open(status.bonnet_open)}")
        print(f"{colored("trunk:", "blue")} {open(status.trunk_open)}")
        print(f"{colored("windows:", "blue")} {open(status.windows_open)}")
        print(f"{colored("lights:", "blue")} {on(status.lights_on)}")
        print(f"{colored("last update:", "blue")} {status.car_captured}")


@cli.command()
@click.argument("vin")
async def air_conditioning(vin):
    """Print current status about air conditioning."""
    async with ClientSession() as session:
        hub = MySkodaHub(session)
        await hub.authenticate(username, password)
        ac = await hub.get_air_conditioning(vin)

        print(f"{colored("window heating:", "blue")} {on(ac.window_heating_enabled)}")
        print(
            f"{colored("window heating (front):", "blue")} {on(ac.window_heating_front_on)}"
        )
        print(
            f"{colored("window heating (back):", "blue")} {on(ac.window_heating_rear_on)}"
        )
        print(
            f"{colored("target temperature:", "blue")} {ac.target_temperature_celsius}°C"
        )
        print(
            f"{colored("steering wheel position:", "blue")} {ac.steering_wheel_position}"
        )
        print(f"{colored("air conditioning:", "blue")} {on(ac.air_conditioning_on)}")
        print(f"{colored("state:", "blue")} {ac.state}")
        print(
            f"{colored("charger:", "blue")} {connected(ac.charger_connected)}, {locked(ac.charger_locked)}"
        )
        print(
            f"{colored("temperature reached:", "blue")} {ac.time_to_reach_target_temperature}"
        )


@cli.command()
@click.argument("vin")
async def position(vin):
    """Print the vehicle's current position."""
    async with ClientSession() as session:
        hub = MySkodaHub(session)
        await hub.authenticate(username, password)
        position = await hub.get_position(vin)

        print(f"{colored("latitude:", "blue")} {position.lat}")
        print(f"{colored("longitude:", "blue")} {position.lng}")
        print(f"{colored("address:", "blue")}")
        print(f"    {position.street} {position.house_number}")
        print(f"    {position.zip_code} {position.city}")
        print(f"    {position.country} ({position.country_code})")


@cli.command()
@click.argument("vin")
async def health(vin):
    """Print the vehicle's mileage."""
    async with ClientSession() as session:
        hub = MySkodaHub(session)
        await hub.authenticate(username, password)
        health = await hub.get_health(vin)

        print(f"{colored("mileage:", "blue")} {health.mileage_in_km}km")
        print(f"{colored("last updated:", "blue")} {health.captured_at}")


@cli.command()
@click.argument("vin")
async def charging(vin):
    """Print the vehicle's current charging state."""
    async with ClientSession() as session:
        hub = MySkodaHub(session)
        await hub.authenticate(username, password)
        charging = await hub.get_charging(vin)

        print(
            f"{colored("battery charge:", "blue")} {charging.status.battery.state_of_charge_in_percent}%"
        )
        print(
            f"{colored("target:", "blue")} {charging.settings.target_state_of_charge_in_percent}%"
        )
        print(
            f"{colored("remaining distance:", "blue")} {charging.status.battery.remaining_cruising_range_in_meters / 1000}km"
        )
        print(f"{colored("charging power:", "blue")} {charging.charge_power_in_kw}kw")
        print(f"{colored("charger type:", "blue")} {charging.charge_type}")
        print(
            f"{colored("charging rate:", "blue")} {charging.charging_rate_in_kilometers_per_hour}km/h"
        )
        print(
            f"{colored("remaining time:", "blue")} {charging.remaining_time_to_fully_charged_in_minutes}min"
        )
        print(f"{colored("state:", "blue")} {charging.status.state}")
        print(
            f"{colored("battery care mode:", "blue")} {on(charging.settings.charging_care_mode is OnOffState.ON)}"
        )
        print(
            f"{colored("reduced current:", "blue")} {on(charging.settings.max_charge_current_ac is MaxChargeCurrent.REDUCED)}"
        )


def open(cond: bool) -> str:
    return colored("open", "red") if cond else colored("closed", "green")


def locked(cond: bool) -> str:
    return colored("locked", "green") if cond else colored("unlocked", "red")


def on(cond: bool) -> str:
    return colored("on", "green") if cond else colored("off", "red")


def connected(cond: bool) -> str:
    return colored("connected", "green") if cond else colored("disconnected", "red")
