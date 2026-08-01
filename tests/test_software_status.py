"""Unit tests for myskoda.models.software_status."""

import pytest

from myskoda.models.software_status import SoftwareStatus, SoftwareUpdateStatus


@pytest.mark.parametrize("status", list(SoftwareStatus))
def test_software_update_status_parsed_ok(status: SoftwareStatus) -> None:
    """Every SoftwareStatus member should deserialize without error.

    Parametrized over the enum itself so any status added in the future is
    covered automatically without touching this test.
    """
    payload = {
        "status": status.value,
        "currentSoftwareVersion": "5.4.4",
        "carCapturedTimestamp": "2026-07-30T20:41:16Z",
        "releaseNotesUrl": (
            "https://content.vw.io/oru/skoda/eu/ota/rn-2025-10-29-rxrc/en-GB/index.html"
        ),
    }

    result = SoftwareUpdateStatus.from_dict(payload)

    assert result.status == status
    assert result.current_software_version == "5.4.4"
    assert result.release_notes_url == payload["releaseNotesUrl"]
