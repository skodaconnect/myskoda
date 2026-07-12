"""Unit tests for vehicle.py update helpers."""

import copy
import json
from datetime import datetime
from pathlib import Path

from myskoda.models.air_conditioning import AirConditioning
from myskoda.models.auxiliary_heating import AuxiliaryHeating
from myskoda.models.charging import Charging
from myskoda.models.chargingprofiles import ChargingProfiles
from myskoda.models.common import BaseResponse
from myskoda.models.departure import DepartureInfo
from myskoda.models.driving_range import DrivingRange
from myskoda.models.status import Status
from myskoda.vehicle import Vehicle, _ts_changed

FIXTURES_DIR = Path(__file__).parent / "fixtures"

OLDER_TIMESTAMP = datetime(2024, 1, 1, 12, 0, 0)  # noqa: DTZ001
NEWER_TIMESTAMP = datetime(2024, 1, 1, 13, 0, 0)  # noqa: DTZ001


def _make_vehicle() -> Vehicle:
    """Create a bare Vehicle instance suitable for testing update methods."""
    v = Vehicle.__new__(Vehicle)
    v.charging = None
    v.status = None
    v.air_conditioning = None
    v.auxiliary_heating = None
    v.charging_profiles = None
    v.driving_range = None
    v.departure_info = None
    return v


def _load(path: str) -> dict:
    return json.loads((FIXTURES_DIR / path).read_text())


def _with_ts(data: dict, ts: str) -> dict:
    d = copy.deepcopy(data)
    d["carCapturedTimestamp"] = ts
    return d


# --- _ts_changed ---


def test_ts_changed_when_existing_is_none() -> None:
    new = BaseResponse(car_captured_timestamp=OLDER_TIMESTAMP)
    assert _ts_changed(None, new) is True


def test_ts_changed_when_timestamps_differ() -> None:
    existing = BaseResponse(car_captured_timestamp=OLDER_TIMESTAMP)
    new = BaseResponse(car_captured_timestamp=NEWER_TIMESTAMP)
    assert _ts_changed(existing, new) is True


def test_ts_changed_when_timestamps_are_equal() -> None:
    existing = BaseResponse(car_captured_timestamp=OLDER_TIMESTAMP)
    new = BaseResponse(car_captured_timestamp=OLDER_TIMESTAMP)
    assert _ts_changed(existing, new) is False


def test_ts_changed_when_new_ts_is_none() -> None:
    existing = BaseResponse(car_captured_timestamp=OLDER_TIMESTAMP)
    new = BaseResponse(car_captured_timestamp=None)
    assert _ts_changed(existing, new) is True


# --- update_charging ---

_CHARGING_RAW = _load("superb/charging-iV.json")


def test_update_charging_when_no_existing_data() -> None:
    v = _make_vehicle()
    new = Charging.from_dict(_CHARGING_RAW)
    assert v.update_charging(new) is True
    assert v.charging is new


def test_update_charging_same_timestamp_skips_update() -> None:
    v = _make_vehicle()
    v.charging = Charging.from_dict(_CHARGING_RAW)
    new = Charging.from_dict(_CHARGING_RAW)
    assert v.update_charging(new) is False


def test_update_charging_new_timestamp_updates() -> None:
    v = _make_vehicle()
    v.charging = Charging.from_dict(_CHARGING_RAW)
    new = Charging.from_dict(_with_ts(_CHARGING_RAW, "2025-01-01T00:00:00Z"))
    assert v.update_charging(new) is True
    assert v.charging is new


# --- update_charging_profiles ---

_CHARGING_PROFILES_RAW = _load("enyaq/charging-profiles.json")


def test_update_charging_profiles_when_no_existing_data() -> None:
    v = _make_vehicle()
    new = ChargingProfiles.from_dict(_CHARGING_PROFILES_RAW)
    assert v.update_charging_profiles(new) is True
    assert v.charging_profiles is new


def test_update_charging_profiles_same_timestamp_skips_update() -> None:
    v = _make_vehicle()
    v.charging_profiles = ChargingProfiles.from_dict(_CHARGING_PROFILES_RAW)
    new = ChargingProfiles.from_dict(_CHARGING_PROFILES_RAW)
    assert v.update_charging_profiles(new) is False


def test_update_charging_profiles_new_timestamp_updates() -> None:
    v = _make_vehicle()
    v.charging_profiles = ChargingProfiles.from_dict(_CHARGING_PROFILES_RAW)
    new = ChargingProfiles.from_dict(_with_ts(_CHARGING_PROFILES_RAW, "2025-01-01T00:00:00Z"))
    assert v.update_charging_profiles(new) is True
    assert v.charging_profiles is new


# --- update_status ---

_STATUS_RAW = _load("superb/vehicle-status-doors-closed.json")


def test_update_status_when_no_existing_data() -> None:
    v = _make_vehicle()
    new = Status.from_dict(_STATUS_RAW)
    assert v.update_status(new) is True
    assert v.status is new


def test_update_status_same_timestamp_skips_update() -> None:
    v = _make_vehicle()
    v.status = Status.from_dict(_STATUS_RAW)
    new = Status.from_dict(_STATUS_RAW)
    assert v.update_status(new) is False


def test_update_status_new_timestamp_updates() -> None:
    v = _make_vehicle()
    v.status = Status.from_dict(_STATUS_RAW)
    new = Status.from_dict(_with_ts(_STATUS_RAW, "2025-01-01T00:00:00Z"))
    assert v.update_status(new) is True
    assert v.status is new


# --- update_air_conditioning ---

_AC_RAW = _load("superb/air-conditioning-idle.json")


def test_update_air_conditioning_when_no_existing_data() -> None:
    v = _make_vehicle()
    new = AirConditioning.from_dict(_AC_RAW)
    assert v.update_air_conditioning(new) is True
    assert v.air_conditioning is new


def test_update_air_conditioning_same_timestamp_skips_update() -> None:
    v = _make_vehicle()
    v.air_conditioning = AirConditioning.from_dict(_AC_RAW)
    new = AirConditioning.from_dict(_AC_RAW)
    assert v.update_air_conditioning(new) is False


def test_update_air_conditioning_new_timestamp_updates() -> None:
    v = _make_vehicle()
    v.air_conditioning = AirConditioning.from_dict(_AC_RAW)
    new = AirConditioning.from_dict(_with_ts(_AC_RAW, "2025-01-01T00:00:00Z"))
    assert v.update_air_conditioning(new) is True
    assert v.air_conditioning is new


# --- update_auxiliary_heating ---

_AUX_RAW = _load("other/auxiliary-heating-idle.json")


def test_update_auxiliary_heating_when_no_existing_data() -> None:
    v = _make_vehicle()
    new = AuxiliaryHeating.from_dict(_AUX_RAW)
    assert v.update_auxiliary_heating(new) is True
    assert v.auxiliary_heating is new


def test_update_auxiliary_heating_same_timestamp_skips_update() -> None:
    v = _make_vehicle()
    v.auxiliary_heating = AuxiliaryHeating.from_dict(_AUX_RAW)
    new = AuxiliaryHeating.from_dict(_AUX_RAW)
    assert v.update_auxiliary_heating(new) is False


def test_update_auxiliary_heating_new_timestamp_updates() -> None:
    v = _make_vehicle()
    v.auxiliary_heating = AuxiliaryHeating.from_dict(_AUX_RAW)
    new = AuxiliaryHeating.from_dict(_with_ts(_AUX_RAW, "2025-01-01T00:00:00Z"))
    assert v.update_auxiliary_heating(new) is True
    assert v.auxiliary_heating is new


# --- update_driving_range ---

_RANGE_RAW = _load("superb/driving-range-car-type-hybrid.json")


def test_update_driving_range_when_no_existing_data() -> None:
    v = _make_vehicle()
    new = DrivingRange.from_dict(_RANGE_RAW)
    assert v.update_driving_range(new) is True
    assert v.driving_range is new


def test_update_driving_range_same_timestamp_skips_update() -> None:
    v = _make_vehicle()
    v.driving_range = DrivingRange.from_dict(_RANGE_RAW)
    new = DrivingRange.from_dict(_RANGE_RAW)
    assert v.update_driving_range(new) is False


def test_update_driving_range_new_timestamp_updates() -> None:
    v = _make_vehicle()
    v.driving_range = DrivingRange.from_dict(_RANGE_RAW)
    new = DrivingRange.from_dict(_with_ts(_RANGE_RAW, "2025-01-01T00:00:00Z"))
    assert v.update_driving_range(new) is True
    assert v.driving_range is new


# --- update_departure_info ---

_DEPARTURE_RAW = _load("other/departure-timers.json")


def test_update_departure_info_when_no_existing_data() -> None:
    v = _make_vehicle()
    new = DepartureInfo.from_dict(_DEPARTURE_RAW)
    assert v.update_departure_info(new) is True
    assert v.departure_info is new


def test_update_departure_info_same_timestamp_skips_update() -> None:
    v = _make_vehicle()
    v.departure_info = DepartureInfo.from_dict(_DEPARTURE_RAW)
    new = DepartureInfo.from_dict(_DEPARTURE_RAW)
    assert v.update_departure_info(new) is False


def test_update_departure_info_new_timestamp_updates() -> None:
    v = _make_vehicle()
    v.departure_info = DepartureInfo.from_dict(_DEPARTURE_RAW)
    new = DepartureInfo.from_dict(_with_ts(_DEPARTURE_RAW, "2025-01-01T00:00:00Z"))
    assert v.update_departure_info(new) is True
    assert v.departure_info is new
