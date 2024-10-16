"""Unit tests for generated fixtures."""

from pathlib import Path

import pytest
from aioresponses import aioresponses

from myskoda.anonymize import VIN
from myskoda.const import BASE_URL_SKODA
from myskoda.models.fixtures import Fixture, FixtureReportGet
from myskoda.myskoda import MySkoda

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.mark.asyncio
async def test_report_get(
    report: FixtureReportGet, responses: aioresponses, myskoda: MySkoda
) -> None:
    responses.get(url=f"{BASE_URL_SKODA}/api{report.url}", body=report.raw)
    result = await myskoda.get_endpoint(VIN, report.endpoint, anonymize=True)

    assert result.result.to_dict() == report.result


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    parameters = []

    for file in FIXTURES_DIR.glob("**/*.yaml"):
        text = file.read_text()
        fixture = Fixture.from_yaml(text)
        if fixture.reports is None:
            continue
        for report in fixture.reports:
            if not report.success:
                continue
            parameters.append(report)

    metafunc.parametrize("report", parameters)
