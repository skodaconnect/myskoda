"""Unit tests for myskoda.models.service_event.

This module partially repeats test_mqtt.py tests but is more isolated:
here we have unit tests for service_event module only.
"""

from pathlib import Path

import pytest

from myskoda.models.service_event import (
    ChargeMode,
    ChargingState,
    ServiceEvent,
    ServiceEventChargingData,
    ServiceEventData,
    ServiceEventError,
    ServiceEventErrorData,
    ServiceEventName,
    ServiceEventWithChargingData,
    ServiceEventWithErrorData,
)

FIXTURES_DIR = Path(__file__).parent.joinpath("fixtures")


@pytest.fixture(name="service_events")
def load_service_events() -> list[str]:
    """Load service_events fixture."""
    service_events = []
    for path in [
        "events/service_event_charging_change_soc.json",
        "events/service_event_charging_charging_status_changed.json",
        "events/service_event_charging_charging_error.json",
        "events/service_event_departure_ready.json",
        "events/service_event_departure_status_changed.json",
        "events/service_event_departure_error_plug.json",
    ]:
        json_file = FIXTURES_DIR / path
        service_events.append(json_file.read_text())
    return service_events


def test_parse_service_events(service_events: list[str]) -> None:
    for service_event in service_events:
        event = ServiceEvent.from_json(service_event)

        if event.name in [
            ServiceEventName.CHANGE_SOC,
            ServiceEventName.CHARGING_STATUS_CHANGED,
        ]:
            try:
                event = ServiceEventWithChargingData.from_json(service_event)
            except ValueError:
                event = ServiceEvent.from_json(service_event)

            if event.name == ServiceEventName.CHANGE_SOC:
                assert event.data == ServiceEventChargingData(
                    charged_range=195,
                    mode=ChargeMode.MANUAL,
                    soc=50,
                    state=ChargingState.CHARGING,
                    time_to_finish=440,
                    user_id="ad0d7945-4814-43d0-801f-change-soc",
                    vin="TMBAXXXXXXXXXXXXX",
                )
            elif event.name == ServiceEventName.CHARGING_STATUS_CHANGED:
                assert event.data == ServiceEventChargingData(
                    user_id=f"ad0d7945-4814-43d0-801f-{event.name.value}",
                    vin="TMBAXXXXXXXXXXXXX",
                )
        elif event.name in [
            ServiceEventName.CHARGING_ERROR,
            ServiceEventName.DEPARTURE_ERROR_PLUG,
        ]:
            try:
                event = ServiceEventWithErrorData.from_json(service_event)
            except ValueError:
                event = ServiceEvent.from_json(service_event)

            if event.name == ServiceEventName.CHARGING_ERROR:
                assert event.data == ServiceEventErrorData(
                    user_id=f"ad0d7945-4814-43d0-801f-{event.name.value}",
                    vin="TMBAXXXXXXXXXXXXX",
                    error_code=ServiceEventError.STOPPED_DEVICE,
                )
            elif event.name == ServiceEventName.DEPARTURE_ERROR_PLUG:
                assert event.data == ServiceEventErrorData(
                    user_id=f"ad0d7945-4814-43d0-801f-{event.name.value}",
                    vin="TMBAXXXXXXXXXXXXX",
                    error_code=ServiceEventError.CLIMA,
                )
        else:
            assert event.data == ServiceEventData(
                user_id=f"ad0d7945-4814-43d0-801f-{event.name.value}",
                vin="TMBAXXXXXXXXXXXXX",
            )
