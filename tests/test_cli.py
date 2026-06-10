"""Unit tests for CLI."""

import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from asyncclick.testing import CliRunner

from myskoda import MySkoda
from myskoda.cli.operations import set_preferred_charging
from myskoda.models.chargingprofiles import ChargingProfiles, ChargingTimes

from .conftest import FIXTURES_DIR

TARGET_VIN = "TMBJM0CKV1N12345"


@pytest.mark.asyncio
async def test_cli_set_preferred_charging_invalid_timer_id() -> None:
    mock = AsyncMock(spec=MySkoda)

    runner = CliRunner()
    result = await runner.invoke(
        set_preferred_charging,
        ["--location", "test", "--id", "5", TARGET_VIN],
        obj={"myskoda": mock},
    )
    assert result.exit_code != 0
    mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_cli_set_preferred_charging_no_parameters() -> None:
    mock = AsyncMock(spec=MySkoda)

    runner = CliRunner()
    result = await runner.invoke(
        set_preferred_charging,
        ["--location", "test", "--id", "4", TARGET_VIN],
        obj={"myskoda": mock},
    )
    assert result.exit_code != 0
    mock.assert_not_awaited()  # no server access for invalid operation


@pytest.mark.asyncio
async def test_cli_set_preferred_charging_incorrect_time() -> None:
    mock = AsyncMock(spec=MySkoda)

    runner = CliRunner()
    result = await runner.invoke(
        set_preferred_charging,
        ["--location", "test", "--id", "4", "--start", "33:12", TARGET_VIN],
        obj={"myskoda": mock},
    )
    assert result.exit_code != 0
    mock.assert_not_awaited()  # no server access for invalid operation


@pytest.fixture(name="charging_profiles")
def load_cli_set_preferred_charging_update_fields() -> list[str]:
    """Load connection status fixture."""
    charging_profiles = []
    for path in [
        "enyaq/charging-profiles.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            charging_profiles.append(file.read())
    return charging_profiles


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("timer_id", "enabled", "start", "end"),
    [
        (1, True, "23:00", "00:15"),
        (2, True, None, "14:53"),
        (3, True, "13:22", None),
        (1, True, None, None),
        (4, None, "23:00", "00:15"),
    ],
)
async def test_cli_set_preferred_charging_update_fields(
    charging_profiles: list[str],
    timer_id: int,
    enabled: bool | None,
    start: str | None,
    end: str | None,
) -> None:
    for charging_profile in charging_profiles:
        charging_profile_json = json.loads(charging_profile)

        location_name = charging_profile_json["currentVehiclePositionProfile"]["name"]
        location_id = charging_profile_json["currentVehiclePositionProfile"]["id"]

        location_json_data = charging_profile_json["chargingProfiles"][location_id - 1]
        start_txt = location_json_data["preferredChargingTimes"][timer_id - 1]["startTime"]
        start_time = datetime.strptime(start_txt, "%H:%M").time()  # noqa: DTZ007
        end_txt = location_json_data["preferredChargingTimes"][timer_id - 1]["endTime"]
        end_time = datetime.strptime(end_txt, "%H:%M").time()  # noqa: DTZ007
        enabled_state = location_json_data["preferredChargingTimes"][timer_id - 1]["enabled"]

        mock = AsyncMock(spec=MySkoda)

        test_data = ChargingProfiles.from_json(charging_profile)
        mock.get_charging_profiles.return_value = test_data

        cli_parameters = [TARGET_VIN]
        cli_parameters += ["--location", location_name]
        cli_parameters += ["--id", timer_id]
        if start is not None:
            cli_parameters += ["--start", start]
            start_time = datetime.strptime(start, "%H:%M").time()  # noqa: DTZ007

        if end is not None:
            cli_parameters += ["--end", end]
            end_time = datetime.strptime(end, "%H:%M").time()  # noqa: DTZ007

        if enabled is not None:
            cli_parameters += ["--enabled", enabled]
            enabled_state = enabled

        charging_times = ChargingTimes(timer_id, enabled_state, start_time, end_time)

        runner = CliRunner()
        result = await runner.invoke(set_preferred_charging, cli_parameters, obj={"myskoda": mock})
        mock.get_charging_profiles.assert_awaited_once()
        mock.set_preferred_charging_times.assert_awaited_once_with(
            TARGET_VIN, location_id, charging_times
        )
        assert result.exit_code == 0
