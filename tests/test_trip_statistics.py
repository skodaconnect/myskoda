"""Tests for trip statistics models."""

import json
from pathlib import Path

import pytest

from myskoda.models.trip_statistics import SingleTrips, TripStatistics

FIXTURES_DIR = Path(__file__).parent.joinpath("fixtures")


def test_parse_single_trips() -> None:
    """Test parsing SingleTrips from real-world fixture."""
    fixture_path = FIXTURES_DIR.joinpath("superb/single-trips-iV.json")
    json_data = fixture_path.read_text()

    parsed = SingleTrips.from_json(json_data)

    assert parsed is not None
    assert parsed.daily_trips is not None
    assert len(parsed.daily_trips) > 0

    raw_data = json.loads(json_data)
    assert parsed.daily_trips[0].date == raw_data["dailyTrips"][0]["date"]

    if parsed.daily_trips[0].trips:
        assert (
            parsed.daily_trips[0].trips[0].end_time
            == raw_data["dailyTrips"][0]["trips"][0]["endTime"]
        )


def test_parse_trip_statistics() -> None:
    """Test parsing TripStatistics from real-world fixture."""
    fixture_path = FIXTURES_DIR.joinpath("superb/trip-statistics-iV.json")
    json_data = fixture_path.read_text()

    parsed = TripStatistics.from_json(json_data)

    assert parsed is not None

    raw_data = json.loads(json_data)
    assert parsed.overall_mileage_in_km == raw_data.get("overallMileageInKm")
    assert parsed.overall_average_speed_in_kmph == raw_data.get("overallAverageSpeedInKmph")


@pytest.fixture(name="single_trip_timezones")
def load_single_trip_timezones() -> str:
    """Load single trip timezone fixture."""
    with FIXTURES_DIR.joinpath("other/single-trip-statistics-timezones.json").open() as file:
        return file.read()


def test_single_trip_utc_helpers(
    single_trip_timezones: str,
) -> None:
    """Test UTC helper properties for trip statistics."""

    result = SingleTrips.from_json(single_trip_timezones)

    daily_trip = result.daily_trips[0]
    assert daily_trip.trips is not None

    trip = daily_trip.trips[1]

    assert trip.start_time == "06:15"
    assert trip.end_time == "06:57"

    assert trip.start_time_utc is not None
    assert trip.end_time_utc is not None

    assert trip.start_time_utc.isoformat() == ("2026-06-09T04:15:09.438000+00:00")
    assert trip.end_time_utc.isoformat() == ("2026-06-09T04:57:00.352000+00:00")


EXPECTED_WAYPOINT_COUNT = 3
EXPECTED_LATITUDE = 52.2
EXPECTED_LONGITUDE = 13.2


def test_single_trip_waypoints_are_parsed(
    single_trip_timezones: str,
) -> None:
    """Test waypoint parsing."""

    result = SingleTrips.from_json(single_trip_timezones)

    daily_trip = result.daily_trips[0]
    assert daily_trip.trips is not None

    trip = daily_trip.trips[1]

    assert trip.waypoints is not None
    assert len(trip.waypoints) == EXPECTED_WAYPOINT_COUNT

    assert trip.waypoints[0].coordinates is not None
    assert trip.waypoints[0].coordinates.latitude == EXPECTED_LATITUDE
    assert trip.waypoints[0].coordinates.longitude == EXPECTED_LONGITUDE
