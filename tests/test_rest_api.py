"""Unit tests for myskoda.rest_api."""

import json
from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from myskoda import RestApi

FIXTURES_DIR = Path(__file__).parent.joinpath("fixtures")

print(f"__file__ = {__file__}")


@pytest.fixture(name="vehicle_info")
def load_vehicle_info() -> str:
    """Load vehicle-info fixture."""
    with FIXTURES_DIR.joinpath("enyaq/garage_vehicles_iv80.json").open() as file:
        return file.read()


@pytest.mark.asyncio
async def test_get_info(vehicle_info: str) -> None:
    """Example unit test for RestAPI.get_info(). Needs more work."""
    vehicle_info_json = json.loads(vehicle_info)
    response_mock = AsyncMock()
    response_mock.text.return_value = vehicle_info
    session_mock = MagicMock()
    session_mock.get.return_value.__aenter__.return_value = response_mock

    api = RestApi(session=session_mock)
    api.idk_session = AsyncMock()
    get_info_result = await api.get_info(vehicle_info_json["vin"])

    # Should probabaly assert the whole thing. Just an example.
    assert get_info_result.name == vehicle_info_json["name"]

    session_mock.get.assert_called_with(
        "https://mysmob.api.connect.skoda-auto.cz/api/v2/garage/vehicles/TMBJM0CKV1N12345"
        "?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3"
        "&connectivityGenerations=MOD4",
        headers=ANY,
    )
