"""Test helpers."""

from collections.abc import AsyncIterator, Generator
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from myskoda.auth.authorization import Authorization
from myskoda.myskoda import MySkoda
from myskoda.rest_api import RestApi


@pytest.fixture(name="responses")
def aioresponses_fixture() -> Generator[aioresponses, None, None]:
    """Return aioresponses fixture."""
    with aioresponses() as mocked_responses:
        yield mocked_responses


@pytest.fixture(name="api")
async def api_fixture() -> AsyncIterator[RestApi]:
    """Return rest api."""
    async with ClientSession() as session:
        authorization = Authorization(session)
        api = RestApi(session, authorization)
        api.authorization.get_access_token = AsyncMock()
        yield api


@pytest.fixture(name="myskoda")
async def myskoda() -> AsyncIterator[MySkoda]:
    """Return rest api."""
    async with ClientSession() as session:
        authorization = Authorization(session)
        api = RestApi(session, authorization)
        api.authorization.get_access_token = AsyncMock()
        api.authorization.authorize = AsyncMock()
        myskoda = MySkoda(session, mqtt_enabled=False)
        myskoda.authorization.get_access_token = AsyncMock()
        myskoda.authorization.authorize = AsyncMock()
        await myskoda.connect("user@example.com", "password")
        yield myskoda
