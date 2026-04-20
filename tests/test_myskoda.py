"""Unit tests for myskoda.py.

Todo:
- Use standard myskoda and myskoda_mqtt_client conftest fixtures."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientSession

from myskoda.myskoda import MySkoda


@pytest.mark.asyncio
async def test_myskoda_connect_initializes_mqtt_lazily() -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session, mqtt_enabled=True)
        fake_mqtt = SimpleNamespace(connect=AsyncMock(), subscribe=lambda _callback: None)
        myskoda.authorization.authorize = AsyncMock()
        myskoda.get_user = AsyncMock(return_value=type("User", (), {"id": "user-id"})())
        myskoda.list_vehicle_vins = AsyncMock(return_value=["vin"])
        myskoda._ensure_mqtt_client = AsyncMock(return_value=fake_mqtt)  # noqa: SLF001

        await myskoda.connect("user@example.com", "password")

        assert myskoda.mqtt is fake_mqtt
        myskoda._ensure_mqtt_client.assert_awaited_once()  # noqa: SLF001
        fake_mqtt.connect.assert_awaited_once_with("user-id", ["vin"])


@pytest.mark.asyncio
async def test_myskoda_enable_mqtt_reuses_cached_fcm_token() -> None:
    async with ClientSession() as session:
        myskoda = MySkoda(session, mqtt_enabled=False)
        first_mqtt = SimpleNamespace(
            connect=AsyncMock(), disconnect=AsyncMock(), subscribe=lambda _cb: None
        )
        second_mqtt = SimpleNamespace(
            connect=AsyncMock(), disconnect=AsyncMock(), subscribe=lambda _cb: None
        )
        myskoda.get_user = AsyncMock(return_value=type("User", (), {"id": "user-id"})())
        myskoda.list_vehicle_vins = AsyncMock(return_value=["vin"])
        myskoda._ensure_mqtt_client = AsyncMock(side_effect=[first_mqtt, second_mqtt])  # noqa: SLF001

        await myskoda.enable_mqtt()
        await myskoda.disconnect()
        myskoda.mqtt = None
        await myskoda.enable_mqtt()

        assert myskoda._ensure_mqtt_client.await_count == 2  # noqa: PLR2004, SLF001
        first_mqtt.connect.assert_awaited_once_with("user-id", ["vin"])
        second_mqtt.connect.assert_awaited_once_with("user-id", ["vin"])
