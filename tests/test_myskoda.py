"""Unit tests for myskoda.py."""

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession

from myskoda.models.event.operation import OperationEvent, OperationName, OperationStatus
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
        myskoda._get_fcm_token = AsyncMock()  # noqa: SLF001

        await myskoda.enable_mqtt(fcm_token="fcm-token")  # noqa: S106

        assert myskoda.mqtt is myskoda_mqtt_client
        assert myskoda_mqtt_client._fcm_token == "test-fcm-token"  # noqa: S105, SLF001
        myskoda._get_fcm_token.assert_not_awaited()  # noqa: SLF001
        assert myskoda.user is not None
        assert myskoda.user.id == "user-id"
        assert myskoda_mqtt_client.user_id == "user-id"
        assert myskoda_mqtt_client.vehicle_vins == ["vin"]
        assert fake_mqtt_client_wrapper.connect_properties_fcm_token == "test-fcm-token"  # noqa: S105


@pytest.mark.asyncio
async def test_process_operation_event_refreshes_charging_profiles_on_success() -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session, mqtt_enabled=False)
        myskoda.refresh_charging_profiles = AsyncMock()

        event = OperationEvent(
            version=1,
            trace_id="trace-id",
            vin="TMOCKAA0AA000000",
            request_id="request-id",
            operation=OperationName.UPDATE_CHARGING_PROFILES,
            status=OperationStatus.COMPLETED_SUCCESS,
        )

        with patch("myskoda.myskoda.asyncio.sleep", new_callable=AsyncMock):
            await myskoda._process_operation_event(event)  # noqa: SLF001

        myskoda.refresh_charging_profiles.assert_awaited_once_with(event.vin)


@pytest.mark.asyncio
async def test_process_operation_event_skips_refresh_on_error() -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session, mqtt_enabled=False)
        myskoda.refresh_charging_profiles = AsyncMock()

        event = OperationEvent(
            version=1,
            trace_id="trace-id",
            vin="TMOCKAA0AA000000",
            request_id="request-id",
            operation=OperationName.UPDATE_CHARGING_PROFILES,
            status=OperationStatus.ERROR,
            error_code="some-error",
        )

        await myskoda._process_operation_event(event)  # noqa: SLF001

        myskoda.refresh_charging_profiles.assert_not_awaited()
