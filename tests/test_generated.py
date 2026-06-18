"""Unit tests for generated fixtures."""

import re
from pathlib import Path

import pytest
from aioresponses import aioresponses

from myskoda.anonymize import VIN
from myskoda.const import BASE_URL_SKODA
from myskoda.models.fixtures import Fixture, FixtureReportGet
from myskoda.myskoda import MySkoda

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _strip_injected_fields(d: dict) -> None:
    """Recursively remove BaseResponse fields that are injected at runtime or absent in fixtures."""
    d.pop("timestamp", None)
    if d.get("car_captured_timestamp") is None:
        d.pop("car_captured_timestamp", None)
    for v in d.values():
        if isinstance(v, dict):
            _strip_injected_fields(v)


@pytest.mark.asyncio
async def test_report_get(
    report: FixtureReportGet, responses: aioresponses, myskoda: MySkoda
) -> None:
    # Check if the URL contains a query string
    if report.url and "?" in report.url:
        url_pattern = re.compile(rf"{BASE_URL_SKODA}/api{report.url.split('?')[0]}\?.*")
    else:
        url_pattern = re.compile(rf"{BASE_URL_SKODA}/api{report.url}")
    responses.get(url=url_pattern, body=report.raw)

    result = await myskoda.get_endpoint(VIN, report.endpoint, anonymize=True)
    result = result.result.to_dict()

    _strip_injected_fields(result)
    if (res := report.result) is not None:
        _strip_injected_fields(res)

    assert result == report.result


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    parameters = []

    for file in FIXTURES_DIR.glob("**/*.yaml"):
        text = file.read_text(encoding="utf-8")
        fixture = Fixture.from_yaml(text)
        if fixture.reports is None:
            continue
        for report in fixture.reports:
            if not report.success:
                continue
            parameters.append(report)

    metafunc.parametrize("report", parameters)
