"""Test helpers."""

from asyncio.timeouts import timeout
from collections.abc import AsyncIterator, Generator
from pathlib import Path
from socket import socket
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses
from amqtt.broker import Broker, CancelledError
from amqtt.client import MQTTClient

from myskoda.auth.authorization import Authorization
from myskoda.myskoda import MySkoda
from myskoda.rest_api import RestApi

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def responses() -> Generator[aioresponses, None, None]:
    """Return aioresponses fixture."""
    with aioresponses() as mocked_responses:
        yield mocked_responses


@pytest.fixture
async def api() -> AsyncIterator[RestApi]:
    """Return rest api."""
    async with ClientSession() as session:
        authorization = Authorization(session)
        api = RestApi(session, authorization)
        api.authorization.get_access_token = AsyncMock()
        yield api


def random_port() -> int:
    with socket() as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


@pytest.fixture
async def broker_port() -> AsyncIterator[int]:
    port = random_port()
    config = {
        "listeners": {
            "default": {
                "type": "tcp",
                "bind": f"127.0.01:{port}",
            },
        },
        "auth": {
            "plugins": ["auth_file"],
            "password-file": str(FIXTURES_DIR / "mqtt" / "mqtt_auth.passwd"),
        },
        "topic-check": {"enabled": False},
    }

    broker = Broker(config)
    await broker.start()
    yield port
    try:
        async with timeout(0.1):
            await broker.shutdown()
    except TimeoutError:
        pass
    except CancelledError:
        pass


@pytest.fixture
async def mqtt_client(broker_port: int) -> AsyncIterator[MQTTClient]:
    client = MQTTClient()
    await client.connect(f"mqtt://admin:example@127.0.0.1:{broker_port}")
    yield client
    await client.disconnect()


@pytest.fixture
async def myskoda(responses: aioresponses, broker_port: int) -> AsyncIterator[MySkoda]:
    """Return rest api."""
    async with ClientSession() as session:
        responses.get(
            url="https://mysmob.api.connect.skoda-auto.cz/api/v1/users",
            body=(FIXTURES_DIR / "mqtt" / "user.json").read_text(),
        )
        responses.get(
            url="https://mysmob.api.connect.skoda-auto.cz/api/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
            body=(FIXTURES_DIR / "mqtt" / "vehicles.json").read_text(),
        )
        myskoda = MySkoda(
            session,
            mqtt_broker_host="127.0.0.1",
            mqtt_broker_port=broker_port,
            mqtt_enable_ssl=False,
        )
        myskoda.authorization.get_access_token = AsyncMock(
            return_value="eyJ0eXAiOiI0ODEyODgzZi05Y2FiLTQwMWMtYTI5OC0wZmEyMTA5Y2ViY2EiLCJhbGciOiJSUzI1NiJ9"
        )
        myskoda.authorization.authorize = AsyncMock()
        await myskoda.connect("user@example.com", "password")
        yield myskoda
        await myskoda.disconnect()
