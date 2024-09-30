"""Unit tests for myskoda.driving_range."""

from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from myskoda import RestApi
from myskoda.auth.authorization import Authorization
from myskoda.models.driving_range import EngineType

FIXTURES_DIR = Path(__file__).parent.joinpath("fixtures")


print(f"__file__ = {__file__}")


@pytest.mark.asyncio
async def test_get_driving_range() -> None:
    """Test case for driving range response."""
    file_name = "superb/driving-range-car-type-hybrid.json"
    vehicle_status = FIXTURES_DIR.joinpath(file_name).read_text()
    response_mock = AsyncMock()
    response_mock.text.return_value = vehicle_status
    session_mock = MagicMock()
    session_mock.get.return_value.__aenter__.return_value = response_mock

    authorization = Authorization(session_mock)
    api = RestApi(session_mock, authorization)
    api.authorization.get_access_token = AsyncMock()
    target_vin = "TMBJM0CKV1N12345"
    get_status_result = await api.get_driving_range(target_vin)

    expected_gasoline_range = 670
    expected_electric_range = 7

    assert get_status_result.car_type == EngineType.HYBRID
    assert get_status_result.primary_engine_range.engine_type == EngineType.GASOLINE
    assert get_status_result.primary_engine_range.remaining_range_in_km == expected_gasoline_range
    assert get_status_result.secondary_engine_range is not None
    assert get_status_result.secondary_engine_range.engine_type == EngineType.ELECTRIC
    assert get_status_result.secondary_engine_range.remaining_range_in_km == expected_electric_range

    session_mock.get.assert_called_with(
        f"https://mysmob.api.connect.skoda-auto.cz/api/v2/vehicle-status/{target_vin}/driving-range",
        headers=ANY,
    )
