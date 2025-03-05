"""Test helpers."""

import json
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

from myskoda.anonymize import ACCESS_TOKEN
from myskoda.myskoda import MySkoda, MySkodaAuthorization
from myskoda.rest_api import RestApi

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TRACE_ID = "7a59299d06535a6756d10e96e0c75ed3"
REQUEST_ID = "b9bc1258-2d0c-43c2-8d67-44d9f6c8cb9f"


@pytest.fixture
def responses() -> Generator[aioresponses, None, None]:
    """Return aioresponses fixture."""
    with aioresponses() as mocked_responses:
        yield mocked_responses


@pytest.fixture
async def api() -> AsyncIterator[RestApi]:
    """Return rest api."""
    async with ClientSession() as session:
        authorization = MySkodaAuthorization(session)
        api = RestApi(session, authorization)
        api.authorization.get_access_token = AsyncMock()
        yield api


def random_port() -> int:
    with socket() as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


def create_broker(port: int) -> Broker:
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

    return Broker(config)


@pytest.fixture
async def broker_port() -> AsyncIterator[int]:
    port = random_port()
    broker = create_broker(port)
    await broker.start()
    yield port
    await kill_broker(broker)


async def kill_broker(broker: Broker) -> None:
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


def mock_default_routes(responses: aioresponses) -> None:
    responses.get(
        url="https://mysmob.api.connect.skoda-auto.cz/api/v1/users",
        body=(FIXTURES_DIR / "mqtt" / "user.json").read_text(),
    )
    responses.get(
        url="https://mysmob.api.connect.skoda-auto.cz/api/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
        body=(FIXTURES_DIR / "mqtt" / "vehicles.json").read_text(),
    )


@pytest.fixture
async def myskoda(responses: aioresponses, broker_port: int) -> AsyncIterator[MySkoda]:
    """Return rest api."""
    async with ClientSession() as session:
        mock_default_routes(responses)
        myskoda = MySkoda(
            session,
            mqtt_broker_host="127.0.0.1",
            mqtt_broker_port=broker_port,
            mqtt_enable_ssl=False,
        )
        myskoda.authorization.get_access_token = AsyncMock(return_value=ACCESS_TOKEN)
        myskoda.authorization.authorize = AsyncMock()
        await myskoda.connect("user@example.com", "password")
        yield myskoda
        await myskoda.disconnect()


def create_completed_json(operation: str) -> bytes:
    return json.dumps(
        {
            "version": 1,
            "operation": operation,
            "status": "COMPLETED_SUCCESS",
            "traceId": TRACE_ID,
            "requestId": REQUEST_ID,
        }
    ).encode("utf-8")
