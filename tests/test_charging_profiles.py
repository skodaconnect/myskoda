"""Tests for charging profile models."""

from myskoda.models.air_conditioning import TimerMode
from myskoda.models.chargingprofiles import ChargingTimers
from myskoda.models.common import Weekday


def test_recurring_charging_timer_deserializes_recurring_days() -> None:
    timer = ChargingTimers.from_dict(
        {
            "id": 1,
            "enabled": True,
            "time": "07:00",
            "type": "RECURRING",
            "recurringOn": ["MONDAY", "FRIDAY"],
        }
    )

    assert timer.type is TimerMode.RECURRING
    assert timer.recurring_on == [Weekday.MONDAY, Weekday.FRIDAY]
    assert timer.one_off_day is None
    assert timer.to_dict(by_alias=True) == {
        "id": 1,
        "enabled": True,
        "time": "07:00",
        "type": "RECURRING",
        "recurringOn": ["MONDAY", "FRIDAY"],
    }


def test_one_off_charging_timer_deserializes_without_recurring_days() -> None:
    timer = ChargingTimers.from_dict(
        {
            "id": 2,
            "enabled": False,
            "time": "12:30",
            "type": "ONE_OFF",
            "oneOffDay": "SUNDAY",
        }
    )

    assert timer.type is TimerMode.ONE_OFF
    assert timer.one_off_day is Weekday.SUNDAY
    assert timer.recurring_on is None
    assert timer.to_dict(by_alias=True) == {
        "id": 2,
        "enabled": False,
        "time": "12:30",
        "type": "ONE_OFF",
        "oneOffDay": "SUNDAY",
    }
