"""Baseic unit tests for operations."""

import pytest
from aioresponses import aioresponses
from amqtt.client import QOS_2, MQTTClient

from myskoda.anonymize import ACCESS_TOKEN, LOCATION, USER_ID, VIN
from myskoda.const import BASE_URL_SKODA
from myskoda.models.air_conditioning import (
    AirConditioningAtUnlock,
    AirConditioningWithoutExternalPower,
    HeaterSource,
    SeatHeating,
    TargetTemperature,
    WindowHeating,
)
from myskoda.models.auxiliary_heating import AuxiliaryConfig, AuxiliaryStartMode
from myskoda.models.charging import ChargeMode
from myskoda.myskoda import MySkoda
from tests.conftest import FIXTURES_DIR, create_completed_json


@pytest.mark.asyncio
async def test_stop_air_conditioning(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/stop"
    responses.post(url=url)

    future = myskoda.stop_air_conditioning(VIN)

    topic = f"{USER_ID}/{VIN}/operation-request/air-conditioning/start-stop-air-conditioning"
    await mqtt_client.publish(topic, create_completed_json("stop-air-conditioning"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json=None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("temperature", "expected"), [(21.5, "21.5"), (23.2, "23.0"), (10.01, "10.0")]
)
async def test_start_air_conditioning(
    responses: aioresponses,
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
    temperature: float,
    expected: str,
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/start"
    responses.post(url=url)

    future = myskoda.start_air_conditioning(VIN, temperature)

    topic = f"{USER_ID}/{VIN}/operation-request/air-conditioning/start-stop-air-conditioning"
    await mqtt_client.publish(topic, create_completed_json("start-air-conditioning"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={
            "heaterSource": "ELECTRIC",
            "targetTemperature": {"temperatureValue": float(expected), "unitInCar": "CELSIUS"},
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("temperature", "expected"), [(21.5, "21.5"), (23.2, "23.0"), (10.01, "10.0")]
)
async def test_set_target_temperature(
    responses: aioresponses,
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
    temperature: float,
    expected: str,
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/settings/target-temperature"
    responses.post(url=url)

    future = myskoda.set_target_temperature(VIN, temperature)

    topic = f"{USER_ID}/{VIN}/operation-request/air-conditioning/set-target-temperature"
    await mqtt_client.publish(
        topic, create_completed_json("set-air-conditioning-target-temperature"), QOS_2
    )

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"temperatureValue": float(expected), "unitInCar": "CELSIUS"},
    )


@pytest.mark.asyncio
async def test_start_window_heating(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/start-window-heating"
    responses.post(url=url)

    future = myskoda.start_window_heating(VIN)

    topic = f"{USER_ID}/{VIN}/operation-request/air-conditioning/start-stop-window-heating"
    await mqtt_client.publish(topic, create_completed_json("start-window-heating"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json=None,
    )


@pytest.mark.asyncio
async def test_stop_window_heating(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/stop-window-heating"
    responses.post(url=url)

    future = myskoda.stop_window_heating(VIN)

    topic = f"{USER_ID}/{VIN}/operation-request/air-conditioning/start-stop-window-heating"
    await mqtt_client.publish(topic, create_completed_json("stop-window-heating"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json=None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [50, 70, 90, 100])
async def test_set_charge_limit(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda, limit: int
) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/charging/{VIN}/set-charge-limit"
    responses.put(url=url)

    future = myskoda.set_charge_limit(VIN, limit)

    topic = f"{USER_ID}/{VIN}/operation-request/charging/update-charge-limit"
    await mqtt_client.publish(topic, create_completed_json("update-charge-limit"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="PUT",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"targetSOCInPercent": limit},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(("enabled", "expected"), [(True, "ACTIVATED"), (False, "DEACTIVATED")])
async def test_set_battery_care_mode(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda, enabled: bool, expected: str
) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/charging/{VIN}/set-care-mode"
    responses.put(url=url)

    future = myskoda.set_battery_care_mode(VIN, enabled)

    topic = f"{USER_ID}/{VIN}/operation-request/charging/update-care-mode"
    await mqtt_client.publish(topic, create_completed_json("update-care-mode"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="PUT",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"chargingCareMode": expected},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(("reduced", "expected"), [(True, "REDUCED"), (False, "MAXIMUM")])
async def test_set_reduced_current_limit(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda, reduced: bool, expected: str
) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/charging/{VIN}/set-charging-current"
    responses.put(url=url)

    future = myskoda.set_reduced_current_limit(VIN, reduced)

    topic = f"{USER_ID}/{VIN}/operation-request/charging/update-charging-current"
    await mqtt_client.publish(topic, create_completed_json("update-charging-current"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="PUT",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"chargingCurrent": expected},
    )


@pytest.mark.asyncio
async def test_start_charging(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda
) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/charging/{VIN}/start"
    responses.post(url=url)

    future = myskoda.start_charging(VIN)

    topic = f"{USER_ID}/{VIN}/operation-request/charging/start-stop-charging"
    await mqtt_client.publish(topic, create_completed_json("start-charging"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json=None,
    )


@pytest.mark.asyncio
async def test_stop_charging(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda
) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/charging/{VIN}/stop"
    responses.post(url=url)

    future = myskoda.stop_charging(VIN)

    topic = f"{USER_ID}/{VIN}/operation-request/charging/start-stop-charging"
    await mqtt_client.publish(topic, create_completed_json("stop-charging"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json=None,
    )


@pytest.mark.asyncio
async def test_wakeup(responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/vehicle-wakeup/{VIN}?applyRequestLimiter=true"
    responses.post(url=url)

    future = myskoda.wakeup(VIN)

    topic = f"{USER_ID}/{VIN}/operation-request/vehicle-wakeup/wakeup"
    await mqtt_client.publish(topic, create_completed_json("wakeup"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json=None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ChargeMode)
async def test_set_charge_mode(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda, mode: ChargeMode
) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/charging/{VIN}/set-charge-mode"
    responses.post(url=url)

    future = myskoda.set_charge_mode(VIN, mode)

    topic = f"{USER_ID}/{VIN}/operation-request/charging/update-charge-mode"
    await mqtt_client.publish(topic, create_completed_json("update-charge-mode"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"chargeMode": mode.value},
    )


@pytest.mark.asyncio
async def test_honk_and_flash(
    responses: aioresponses,
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/vehicle-access/{VIN}/honk-and-flash"
    responses.post(url=url)

    lat = LOCATION["latitude"]
    lng = LOCATION["longitude"]

    responses.get(
        url=f"{BASE_URL_SKODA}/api/v1/maps/positions?vin={VIN}",
        body=(FIXTURES_DIR / "enyaq" / "positions.json").read_text(),
    )

    future = myskoda.honk_flash(VIN)

    topic = f"{USER_ID}/{VIN}/operation-request/vehicle-access/honk-and-flash"
    await mqtt_client.publish(topic, create_completed_json("start-honk"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"mode": "HONK_AND_FLASH", "vehiclePosition": {"latitude": lat, "longitude": lng}},
    )


@pytest.mark.asyncio
async def test_flash(
    responses: aioresponses,
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/vehicle-access/{VIN}/honk-and-flash"
    responses.post(url=url)

    lat = LOCATION["latitude"]
    lng = LOCATION["longitude"]

    responses.get(
        url=f"{BASE_URL_SKODA}/api/v1/maps/positions?vin={VIN}",
        body=(FIXTURES_DIR / "enyaq" / "positions.json").read_text(),
    )

    future = myskoda.flash(VIN)

    topic = f"{USER_ID}/{VIN}/operation-request/vehicle-access/honk-and-flash"
    await mqtt_client.publish(topic, create_completed_json("start-flash"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"mode": "FLASH", "vehiclePosition": {"latitude": lat, "longitude": lng}},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("spin", ["1234", "4321"])
async def test_lock(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda, spin: str
) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/vehicle-access/{VIN}/lock"
    responses.post(url=url)

    future = myskoda.lock(VIN, spin)

    topic = f"{USER_ID}/{VIN}/operation-request/vehicle-access/lock-vehicle"
    await mqtt_client.publish(topic, create_completed_json("lock"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"currentSpin": spin},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("spin", ["1234", "4321"])
async def test_unlock(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda, spin: str
) -> None:
    url = f"{BASE_URL_SKODA}/api/v1/vehicle-access/{VIN}/unlock"
    responses.post(url=url)

    future = myskoda.unlock(VIN, spin)

    topic = f"{USER_ID}/{VIN}/operation-request/vehicle-access/lock-vehicle"
    await mqtt_client.publish(topic, create_completed_json("unlock"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"currentSpin": spin},
    )


@pytest.mark.asyncio
async def test_stop_auxiliary_heater(
    responses: aioresponses, mqtt_client: MQTTClient, myskoda: MySkoda
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/auxiliary-heating/stop"
    responses.post(url=url)

    future = myskoda.stop_auxiliary_heating(VIN)

    topic = f"{USER_ID}/{VIN}/operation-request/auxiliary-heating/start-stop-auxiliary-heating"
    await mqtt_client.publish(topic, create_completed_json("stop-auxiliary-heating"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json=None,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("spin", "config", "expected"),
    [
        ("1234", AuxiliaryConfig(TargetTemperature(temperature_value=22.3)), "22.5"),
        ("1234", AuxiliaryConfig(duration_in_seconds=600), "600"),
        ("1234", AuxiliaryConfig(start_mode=AuxiliaryStartMode.HEATING), "HEATING"),
        ("1234", AuxiliaryConfig(heater_source=HeaterSource.AUTOMATIC), "AUTOMATIC"),
    ],
)
async def test_start_auxiliary_heater(  # noqa: PLR0913
    responses: aioresponses,
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
    spin: str,
    config: AuxiliaryConfig,
    expected: str,
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/auxiliary-heating/start"
    responses.post(url=url)

    future = myskoda.start_auxiliary_heating(VIN, spin, config)

    topic = f"{USER_ID}/{VIN}/operation-request/auxiliary-heating/start-stop-auxiliary-heating"
    await mqtt_client.publish(topic, create_completed_json("start-auxiliary-heating"), QOS_2)

    json_data: dict[str, object] = {"spin": spin}
    if config is not None:
        if config.target_temperature is not None:
            json_data["targetTemperature"] = {
                "temperatureValue": float(expected),
                "unitInCar": "CELSIUS",
            }
        if config.duration_in_seconds is not None:
            json_data["durationInSeconds"] = int(expected)
        if config.heater_source is not None:
            json_data["heaterSource"] = expected
        if config.start_mode is not None:
            json_data["startMode"] = expected

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json=json_data,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("settings", "expected"),
    [
        (
            AirConditioningWithoutExternalPower(
                air_conditioning_without_external_power_enabled=True
            ),
            True,
        ),
        (
            AirConditioningWithoutExternalPower(
                air_conditioning_without_external_power_enabled=False
            ),
            False,
        ),
    ],
)
async def test_set_ac_without_external_power(
    responses: aioresponses,
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
    settings: AirConditioningWithoutExternalPower,
    expected: bool,
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/settings/ac-without-external-power"
    responses.post(url=url)

    future = myskoda.set_ac_without_external_power(VIN, settings)

    topic = (
        f"{USER_ID}/{VIN}/operation-request/"
        "air-conditioning/set-air-conditioning-without-external-power"
    )
    await mqtt_client.publish(
        topic, create_completed_json("set-air-conditioning-without-external-power"), QOS_2
    )

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"airConditioningWithoutExternalPowerEnabled": expected},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("settings", "expected"),
    [
        (AirConditioningAtUnlock(air_conditioning_at_unlock_enabled=True), True),
        (AirConditioningAtUnlock(air_conditioning_at_unlock_enabled=False), False),
    ],
)
async def test_set_ac_at_unlock(
    responses: aioresponses,
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
    settings: AirConditioningAtUnlock,
    expected: bool,
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/settings/ac-at-unlock"
    responses.post(url=url)

    future = myskoda.set_ac_at_unlock(VIN, settings)

    topic = f"{USER_ID}/{VIN}/operation-request/" "air-conditioning/set-air-conditioning-at-unlock"
    await mqtt_client.publish(topic, create_completed_json("set-air-conditioning-at-unlock"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"airConditioningAtUnlockEnabled": expected},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("settings", "expected"),
    [
        (WindowHeating(window_heating_enabled=True), True),
        (WindowHeating(window_heating_enabled=False), False),
    ],
)
async def test_set_windows_heating(
    responses: aioresponses,
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
    settings: WindowHeating,
    expected: bool,
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/settings/windows-heating"
    responses.post(url=url)

    future = myskoda.set_windows_heating(VIN, settings)

    topic = f"{USER_ID}/{VIN}/operation-request/" "air-conditioning/windows-heating"
    await mqtt_client.publish(topic, create_completed_json("windows-heating"), QOS_2)

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json={"windowHeatingEnabled": expected},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("settings", "expected"),
    [
        (SeatHeating(front_left=True), True),
        (SeatHeating(front_right=True), True),
        (SeatHeating(front_left=False), False),
    ],
)
async def test_set_seats_heating(
    responses: aioresponses,
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
    settings: SeatHeating,
    expected: bool,
) -> None:
    url = f"{BASE_URL_SKODA}/api/v2/air-conditioning/{VIN}/settings/seats-heating"
    responses.post(url=url)

    future = myskoda.set_seats_heating(VIN, settings)

    topic = (
        f"{USER_ID}/{VIN}/operation-request/" "air-conditioning/set-air-conditioning-seats-heating"
    )
    await mqtt_client.publish(
        topic, create_completed_json("set-air-conditioning-seats-heating"), QOS_2
    )

    json_data: dict[str, object] = {}
    if settings is not None:
        if settings.front_left is not None:
            json_data["frontLeft"] = expected
        if settings.front_right is not None:
            json_data["frontRight"] = expected

    await future
    responses.assert_called_with(
        url=url,
        method="POST",
        headers={"authorization": f"Bearer {ACCESS_TOKEN}"},
        json=json_data,
    )
