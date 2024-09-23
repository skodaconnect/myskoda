"""Unit tests for myskoda.rest_api."""

import json
from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from myskoda import RestApi
from myskoda.auth.authorization import Authorization

FIXTURES_DIR = Path(__file__).parent.joinpath("fixtures")

print(f"__file__ = {__file__}")


@pytest.fixture(name="vehicle_infos")
def load_vehicle_info() -> list[str]:
    """Load vehicle-info fixture."""
    vehicle_infos = []
    # TODO @dvx76: probably just glob all files
    for path in [
        "enyaq/garage_vehicles_iv80.json",
        "enyaq/garage_vehicles_iv80_coupe.json",
        "superb/garage_vehicles_LK_liftback.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            vehicle_infos.append(file.read())
    return vehicle_infos


@pytest.mark.asyncio
async def test_get_info(vehicle_infos: list[str]) -> None:
    """Example unit test for RestAPI.get_info(). Needs more work."""
    for vehicle_info in vehicle_infos:
        vehicle_info_json = json.loads(vehicle_info)
        response_mock = AsyncMock()
        response_mock.text.return_value = vehicle_info
        session_mock = MagicMock()
        session_mock.get.return_value.__aenter__.return_value = response_mock

        authorization = Authorization(session_mock)
        api = RestApi(session_mock, authorization)
        api.authorization.get_access_token = AsyncMock()
        get_info_result = await api.get_info(vehicle_info_json["vin"])

        # Should probabaly assert the whole thing. Just an example.
        assert get_info_result.name == vehicle_info_json["name"]

        session_mock.get.assert_called_with(
            "https://mysmob.api.connect.skoda-auto.cz/api/v2/garage/vehicles/TMBJM0CKV1N12345"
            "?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3"
            "&connectivityGenerations=MOD4",
            headers=ANY,
        )
