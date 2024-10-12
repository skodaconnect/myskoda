"""Unit tests for generated fixtures."""

from os import listdir
from pathlib import Path

import pytest
from aioresponses import aioresponses
from yaml import safe_load

from myskoda.const import BASE_URL_SKODA
from myskoda.rest_api import RestApi

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "gen"

vehicle_dirs = list(listdir(FIXTURES_DIR))
names = {}


def read_test_info(vehicle: str, test: str, endpoint: str) -> tuple[dict, dict, str, dict]:
    path = FIXTURES_DIR / vehicle / test
    meta = safe_load((path / "meta.yaml").read_text())
    request = safe_load((path / endpoint / "request.yaml").read_text())
    raw = (path / endpoint / "raw.json").read_text()
    parsed = safe_load((path / endpoint / "parsed.yaml").read_text())
    return (meta, request, raw, parsed)


@pytest.mark.asyncio
async def test_air_conditioning(
    vehicle: str, test: str, responses: aioresponses, api: RestApi
) -> None:
    if not (FIXTURES_DIR / vehicle / test / "air_conditioning").is_dir():
        return

    (meta, request, raw, parsed) = read_test_info(vehicle, test, "air_conditioning")

    responses.get(url=f"{BASE_URL_SKODA}/api{request["url"]}", body=raw)
    result = await api.get_air_conditioning(meta["vehicle"]["vin"])

    assert result.to_dict() == parsed


@pytest.mark.asyncio
async def test_charging(vehicle: str, test: str, responses: aioresponses, api: RestApi) -> None:
    if not (FIXTURES_DIR / vehicle / test / "charging").is_dir():
        return

    (meta, request, raw, parsed) = read_test_info(vehicle, test, "charging")

    responses.get(url=f"{BASE_URL_SKODA}/api{request["url"]}", body=raw)
    result = await api.get_charging(meta["vehicle"]["vin"])

    assert result.to_dict() == parsed


@pytest.mark.asyncio
async def test_driving_range(
    vehicle: str, test: str, responses: aioresponses, api: RestApi
) -> None:
    if not (FIXTURES_DIR / vehicle / test / "driving_range").is_dir():
        return

    (meta, request, raw, parsed) = read_test_info(vehicle, test, "driving_range")

    responses.get(url=f"{BASE_URL_SKODA}/api{request["url"]}", body=raw)
    result = await api.get_driving_range(meta["vehicle"]["vin"])

    assert result.to_dict() == parsed


@pytest.mark.asyncio
async def test_health(vehicle: str, test: str, responses: aioresponses, api: RestApi) -> None:
    if not (FIXTURES_DIR / vehicle / test / "health").is_dir():
        return

    (meta, request, raw, parsed) = read_test_info(vehicle, test, "health")

    responses.get(url=f"{BASE_URL_SKODA}/api{request["url"]}", body=raw)
    result = await api.get_health(meta["vehicle"]["vin"])

    assert result.to_dict() == parsed


@pytest.mark.asyncio
async def test_info(vehicle: str, test: str, responses: aioresponses, api: RestApi) -> None:
    if not (FIXTURES_DIR / vehicle / test / "info").is_dir():
        return

    (meta, request, raw, parsed) = read_test_info(vehicle, test, "info")

    responses.get(url=f"{BASE_URL_SKODA}/api{request["url"]}", body=raw)
    result = await api.get_info(meta["vehicle"]["vin"])

    assert result.to_dict() == parsed


@pytest.mark.asyncio
async def test_maintenance(vehicle: str, test: str, responses: aioresponses, api: RestApi) -> None:
    if not (FIXTURES_DIR / vehicle / test / "maintenance").is_dir():
        return

    (meta, request, raw, parsed) = read_test_info(vehicle, test, "maintenance")

    responses.get(url=f"{BASE_URL_SKODA}/api{request["url"]}", body=raw)
    result = await api.get_maintenance(meta["vehicle"]["vin"])

    assert result.to_dict() == parsed


@pytest.mark.asyncio
async def test_positions(vehicle: str, test: str, responses: aioresponses, api: RestApi) -> None:
    if not (FIXTURES_DIR / vehicle / test / "positions").is_dir():
        return

    (meta, request, raw, parsed) = read_test_info(vehicle, test, "positions")

    responses.get(url=f"{BASE_URL_SKODA}/api{request["url"]}", body=raw)
    result = await api.get_positions(meta["vehicle"]["vin"])

    assert result.to_dict() == parsed


@pytest.mark.asyncio
async def test_status(vehicle: str, test: str, responses: aioresponses, api: RestApi) -> None:
    if not (FIXTURES_DIR / vehicle / test / "status").is_dir():
        return

    (meta, request, raw, parsed) = read_test_info(vehicle, test, "status")

    responses.get(url=f"{BASE_URL_SKODA}/api{request["url"]}", body=raw)
    result = await api.get_status(meta["vehicle"]["vin"])

    assert result.to_dict() == parsed


@pytest.mark.asyncio
async def test_trip_statistics(
    vehicle: str, test: str, responses: aioresponses, api: RestApi
) -> None:
    if not (FIXTURES_DIR / vehicle / test / "trip_statistics").is_dir():
        return

    (meta, request, raw, parsed) = read_test_info(vehicle, test, "trip_statistics")

    responses.get(url=f"{BASE_URL_SKODA}/api{request["url"]}", body=raw)
    result = await api.get_trip_statistics(meta["vehicle"]["vin"])

    assert result.to_dict() == parsed


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    parameters = [
        (vehicle_dir, test_name)
        for vehicle_dir in listdir(FIXTURES_DIR)
        for test_name in listdir(FIXTURES_DIR / vehicle_dir)
    ]

    metafunc.parametrize("vehicle,test", parameters)
