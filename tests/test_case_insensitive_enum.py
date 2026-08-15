"""Tests for lenient enum handling of unknown API values."""

import logging

import pytest

from myskoda.models.charging import ChargingState
from myskoda.models.software_status import SoftwareStatus, SoftwareUpdateStatus


def test_unknown_value_is_preserved_as_pseudo_member() -> None:
    """An unrecognized value becomes a member carrying the raw string."""
    member = SoftwareStatus("SOME_FUTURE_STATUS")
    assert member.value == "SOME_FUTURE_STATUS"
    assert str(member) == "SOME_FUTURE_STATUS"
    assert isinstance(member, SoftwareStatus)
    assert member.name not in SoftwareStatus.__members__


def test_unknown_value_pseudo_members_are_singletons() -> None:
    """The same unknown value always resolves to the same pseudo-member."""
    assert SoftwareStatus("SOME_FUTURE_STATUS") is SoftwareStatus("SOME_FUTURE_STATUS")


def test_unknown_value_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    """A warning is logged when a new value is encountered."""
    with caplog.at_level(logging.WARNING):
        SoftwareStatus("LOG_ME_STATUS")
    assert "LOG_ME_STATUS" in caplog.text


def test_case_insensitive_match_still_wins() -> None:
    """Known values keep matching case-insensitively."""
    assert SoftwareStatus("update_in_progress") is SoftwareStatus.UPDATE_IN_PROGRESS


def test_unrecognized_status_deserializes_without_raising() -> None:
    """A novel server-side status deserializes and keeps its raw value."""
    result = SoftwareUpdateStatus.from_json(
        '{"status":"BRAND_NEW","currentSoftwareVersion":"1.2.3"}'
    )
    assert result.status.value == "BRAND_NEW"
    assert result.status.name not in SoftwareStatus.__members__


def test_unknown_status_serializes_raw_value() -> None:
    """Serializing keeps the raw unknown value."""
    result = SoftwareUpdateStatus.from_json(
        '{"status":"BRAND_NEW","currentSoftwareVersion":"1.2.3"}'
    )
    assert result.to_dict()["status"] == "BRAND_NEW"


def test_enum_without_lenient_base_stays_strict() -> None:
    """Enums not inheriting LenientStrEnum keep raising on unknown values."""
    with pytest.raises(ValueError, match="is not a valid"):
        ChargingState("NOT_A_REAL_STATE")
