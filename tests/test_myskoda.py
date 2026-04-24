"""Unit tests for myskoda.py."""

from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientSession

from myskoda.mqtt import MySkodaMqttClient
from myskoda.myskoda import MySkoda
from tests.conftest import FakeMqttClientWrapper


@pytest.mark.asyncio
async def test_myskoda_connect_requires_credentials() -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session)

        with pytest.raises(TypeError, match="requires refresh_token"):
            await myskoda.connect()


@pytest.mark.asyncio
async def test_myskoda_connect_authorizes_with_email_password_and_enables_mqtt() -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session, mqtt_enabled=True)
        myskoda.authorization.authorize = AsyncMock()
        myskoda.authorization.authorize_refresh_token = AsyncMock()
        myskoda.enable_mqtt = AsyncMock()

        await myskoda.connect("user@example.com", "password")

        myskoda.authorization.authorize.assert_awaited_once_with("user@example.com", "password")
        myskoda.authorization.authorize_refresh_token.assert_not_awaited()
        myskoda.enable_mqtt.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_myskoda_connect_authorizes_with_refresh_token_and_enables_mqtt() -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session, mqtt_enabled=True)
        myskoda.authorization.authorize = AsyncMock()
        myskoda.authorization.authorize_refresh_token = AsyncMock()
        myskoda.enable_mqtt = AsyncMock()

        await myskoda.connect(refresh_token="refresh-token")  # noqa: S106

        myskoda.authorization.authorize_refresh_token.assert_awaited_once_with("refresh-token")
        myskoda.authorization.authorize.assert_not_awaited()
        myskoda.enable_mqtt.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_myskoda_connect_passes_fcm_token_to_enable_mqtt() -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session, mqtt_enabled=True)
        myskoda.authorization.authorize = AsyncMock()
        myskoda.enable_mqtt = AsyncMock()

        await myskoda.connect("user@example.com", "password", fcm_token="fcm-token")  # noqa: S106

        assert myskoda.fcm_token == "fcm-token"  # noqa: S105
        myskoda.enable_mqtt.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_myskoda_connect_skips_mqtt_when_disabled() -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session, mqtt_enabled=False)
        myskoda.authorization.authorize = AsyncMock()
        myskoda.enable_mqtt = AsyncMock()

        await myskoda.connect("user@example.com", "password")

        myskoda.authorization.authorize.assert_awaited_once_with("user@example.com", "password")
        myskoda.enable_mqtt.assert_not_awaited()


@pytest.mark.asyncio
async def test_myskoda_enable_mqtt_uses_existing_mqtt_client(
    myskoda_mqtt_client: MySkodaMqttClient,
    fake_mqtt_client_wrapper: FakeMqttClientWrapper,
) -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session, mqtt_enabled=False)
        myskoda.mqtt = myskoda_mqtt_client
        myskoda.get_user = AsyncMock(return_value=type("User", (), {"id": "user-id"})())
        myskoda.list_vehicle_vins = AsyncMock(return_value=["vin"])
        myskoda.get_and_register_fcm_token = AsyncMock()

        await myskoda.enable_mqtt(fcm_token="fcm-token")  # noqa: S106

        assert myskoda.mqtt is myskoda_mqtt_client
        assert myskoda_mqtt_client.fcm_token == "test-fcm-token"  # noqa: S105
        myskoda.get_and_register_fcm_token.assert_not_awaited()
        assert myskoda.user is not None
        assert myskoda.user.id == "user-id"
        assert myskoda_mqtt_client.user_id == "user-id"
        assert myskoda_mqtt_client.vehicle_vins == ["vin"]
        assert fake_mqtt_client_wrapper.connect_properties_fcm_token == "test-fcm-token"  # noqa: S105


@pytest.mark.asyncio
async def test_myskoda_enable_mqtt_creates_mqtt_client_with_cached_fcm_token(
    fake_mqtt_client_wrapper: FakeMqttClientWrapper,
) -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session, mqtt_enabled=False)
        myskoda.fcm_token = "cached-token"  # noqa: S105
        myskoda.authorization.get_access_token = AsyncMock(return_value="access-token")
        myskoda.get_user = AsyncMock(return_value=type("User", (), {"id": "user-id"})())
        myskoda.list_vehicle_vins = AsyncMock(return_value=["vin"])
        myskoda.get_and_register_fcm_token = AsyncMock()

        myskoda.mqtt = MySkodaMqttClient(
            authorization=myskoda.authorization,
            fcm_token=myskoda.fcm_token,
            mqtt_client=fake_mqtt_client_wrapper,
        )

        await myskoda.enable_mqtt()

        myskoda.get_and_register_fcm_token.assert_not_awaited()
        assert myskoda.mqtt is not None
        assert myskoda.mqtt.fcm_token == "cached-token"  # noqa: S105
        assert myskoda.mqtt.user_id == "user-id"
        assert myskoda.mqtt.vehicle_vins == ["vin"]
        assert fake_mqtt_client_wrapper.connect_properties_fcm_token == "cached-token"  # noqa: S105
