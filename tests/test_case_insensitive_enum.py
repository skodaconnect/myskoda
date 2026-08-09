"""Tests for CaseInsensitiveStrEnum unknown-value handling."""

import pytest

from myskoda.models.charging import ChargingState
from myskoda.models.software_status import SoftwareStatus, SoftwareUpdateStatus


def test_unknown_value_falls_back_to_unknown_member() -> None:
    """An unrecognized value resolves to UNKNOWN instead of raising."""
    assert SoftwareStatus("SOME_FUTURE_STATUS") is SoftwareStatus.UNKNOWN


def test_case_insensitive_match_still_wins_over_unknown() -> None:
    """A known value keeps matching case-insensitively, not falling back."""
    assert SoftwareStatus("update_in_progress") is SoftwareStatus.UPDATE_IN_PROGRESS


def test_unrecognized_status_deserializes_without_raising() -> None:
    """A novel server-side status no longer breaks model deserialization."""
    result = SoftwareUpdateStatus.from_json(
        '{"status":"BRAND_NEW","currentSoftwareVersion":"1.2.3"}'
    )
    assert result.status is SoftwareStatus.UNKNOWN


def test_enum_without_unknown_member_stays_strict() -> None:
    """Enums that define no UNKNOWN member keep the previous strict behavior."""
    with pytest.raises(ValueError, match="is not a valid"):
        ChargingState("NOT_A_REAL_STATE")
