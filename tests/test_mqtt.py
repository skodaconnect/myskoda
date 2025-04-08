"""Unit tests for MQTT."""

import json
from asyncio import get_event_loop
from datetime import datetime
from pathlib import Path
from unittest.mock import ANY

import pytest
from amqtt.client import QOS_2, MQTTClient

from myskoda.anonymize import USER_ID, VIN
from myskoda.event import (
    Event,
    EventAccess,
    EventCharging,
    EventLights,
    EventOdometer,
    EventOperation,
    EventVehicleConnectionStatusUpdate,
    EventVehicleIgnitionStatus,
)
from myskoda.models.charging import ChargeMode, ChargingState
from myskoda.models.operation_request import OperationName, OperationRequest, OperationStatus
from myskoda.models.service_event import (
    ServiceEvent,
    ServiceEventChargingData,
    ServiceEventData,
    ServiceEventName,
    ServiceEventWithChargingData,
)
from myskoda.models.vehicle_event import (
    IgnitionStatus,
    VehicleEvent,
    VehicleEventData,
    VehicleEventName,
    VehicleEventVehicleIgnitionStatusData,
    VehicleEventWithVehicleIgnitionStatusData,
)
from myskoda.myskoda import MySkoda

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_wait_for_operation(
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
) -> None:
    assert myskoda.mqtt is not None

    topic = f"{USER_ID}/{VIN}/operation-request/air-conditioning/start-stop-air-conditioning"

    future = myskoda.mqtt.wait_for_operation(OperationName.START_AIR_CONDITIONING)

    await mqtt_client.publish(
        topic,
        b'{"version":1,"operation":"start-air-conditioning","status":"IN_PROGRESS","traceId":"f0b638f7bba08ec4acb5de64cdb97ba9","requestId":"72f24950-b3db-4b7e-948f-7032f533773a"}',
        QOS_2,
    )

    assert future.done() is False

    await mqtt_client.publish(
        topic,
        b'{"version":1,"operation":"start-air-conditioning","status":"COMPLETED_SUCCESS","traceId":"10d37beb6b37e9a9e74460d402855f27","requestId":"72f24950-b3db-4b7e-948f-7032f533773a"}',
        QOS_2,
    )

    await future


@pytest.mark.asyncio
async def test_subscribe_event(
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
) -> None:
    assert myskoda.mqtt is not None

    base_topic = f"{USER_ID}/{VIN}"
    trace_id = "7a59299d06535a6756d10e96e0c75ed3"
    request_id = "b9bc1258-2d0c-43c2-8d67-44d9f6c8cb9f"
    timestamp_str = "2024-10-17T08:49:59.538Z"
    timestamp = datetime.fromisoformat(timestamp_str)

    events: list[Event] = []
    future = get_event_loop().create_future()

    messages = [
        (
            f"{base_topic}/operation-request/air-conditioning/start-stop-air-conditioning",
            json.dumps(
                {
                    "version": 1,
                    "operation": "stop-air-conditioning",
                    "status": "COMPLETED_SUCCESS",
                    "traceId": trace_id,
                    "requestId": request_id,
                }
            ),
        ),
        (
            f"{base_topic}/service-event/vehicle-status/lights",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "change-lights",
                    "data": {
                        "userId": USER_ID,
                        "vin": VIN,
                    },
                }
            ),
        ),
        (
            f"{base_topic}/service-event/vehicle-status/odometer",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "change-odometer",
                    "data": {
                        "userId": USER_ID,
                        "vin": VIN,
                    },
                }
            ),
        ),
        (
            f"{base_topic}/service-event/vehicle-status/access",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "change-access",
                    "data": {
                        "userId": USER_ID,
                        "vin": VIN,
                    },
                }
            ),
        ),
        (
            f"{base_topic}/service-event/charging",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "change-soc",
                    "data": {
                        "mode": "manual",
                        "state": "charging",
                        "soc": "91",
                        "chargedRange": "307",
                        "timeToFinish": "40",
                        "userId": USER_ID,
                        "vin": VIN,
                    },
                }
            ),
        ),
        (
            f"{base_topic}/service-event/charging",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "charging-completed",
                    "data": {
                        "mode": "manual",
                        "state": "chargePurposeReachedAndConservation",
                        "soc": "100",
                        "chargedRange": "500",
                        "timeToFinish": "0",
                        "userId": USER_ID,
                        "vin": VIN,
                    },
                }
            ),
        ),
        (
            f"{base_topic}/service-event/charging",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "charging-completed",
                    "data": {
                        "userId": USER_ID,
                        "vin": VIN,
                    },
                }
            ),
        ),
        (
            f"{base_topic}/vehicle-event/vehicle-connection-status-update",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "vehicle-connection-online",
                    "data": {
                        "userId": USER_ID,
                        "vin": VIN,
                    },
                }
            ),
        ),
        (
            f"{base_topic}/vehicle-event/vehicle-connection-status-update",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "vehicle-awake",
                    "data": {
                        "userId": USER_ID,
                        "vin": VIN,
                    },
                }
            ),
        ),
        (
            f"{base_topic}/vehicle-event/vehicle-connection-status-update",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "vehicle-warning-batterylevel",
                    "data": {
                        "userId": USER_ID,
                        "vin": VIN,
                    },
                }
            ),
        ),
        (
            f"{base_topic}/vehicle-event/vehicle-ignition-status",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "vehicle-ignition-status-changed",
                    "data": {
                        "userId": USER_ID,
                        "vin": VIN,
                        "ignitionStatus": IgnitionStatus.ON,
                    },
                }
            ),
        ),
        (
            f"{base_topic}/vehicle-event/vehicle-ignition-status",
            json.dumps(
                {
                    "version": 1,
                    "traceId": trace_id,
                    "timestamp": timestamp_str,
                    "producer": "SKODA_MHUB",
                    "name": "vehicle-ignition-status-changed",
                    "data": {
                        "userId": USER_ID,
                        "vin": VIN,
                        "ignitionStatus": IgnitionStatus.OFF,
                    },
                }
            ),
        ),
    ]

    async def on_event(event: Event) -> None:
        events.append(event)
        if len(events) == len(messages):
            future.set_result(None)

    myskoda.subscribe_events(on_event)

    for topic, message in messages:
        await mqtt_client.publish(topic, message.encode("utf-8"), QOS_2)

    await future

    assert events == [
        EventOperation(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            operation=OperationRequest(
                version=1,
                operation=OperationName.STOP_AIR_CONDITIONING,
                trace_id=trace_id,
                request_id=request_id,
                status=OperationStatus.COMPLETED_SUCCESS,
                error_code=None,
            ),
        ),
        EventLights(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=ServiceEvent(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=ServiceEventName.CHANGE_LIGHTS,
                data=ServiceEventData(user_id=USER_ID, vin=VIN),
            ),
        ),
        EventOdometer(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=ServiceEvent(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=ServiceEventName.CHANGE_ODOMETER,
                data=ServiceEventData(user_id=USER_ID, vin=VIN),
            ),
        ),
        EventAccess(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=ServiceEvent(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=ServiceEventName.CHANGE_ACCESS,
                data=ServiceEventData(user_id=USER_ID, vin=VIN),
            ),
        ),
        EventCharging(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=ServiceEventWithChargingData(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=ServiceEventName.CHANGE_SOC,
                data=ServiceEventChargingData(
                    user_id=USER_ID,
                    vin=VIN,
                    charged_range=307,
                    soc=91,
                    state=ChargingState.CHARGING,
                    mode=ChargeMode.MANUAL,
                    time_to_finish=40,
                ),
            ),
        ),
        EventCharging(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=ServiceEventWithChargingData(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=ServiceEventName.CHARGING_COMPLETED,
                data=ServiceEventChargingData(
                    user_id=USER_ID,
                    vin=VIN,
                    charged_range=500,
                    soc=100,
                    state=ChargingState.CONSERVING,
                    mode=ChargeMode.MANUAL,
                    time_to_finish=0,
                ),
            ),
        ),
        EventCharging(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=ServiceEventWithChargingData(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=ServiceEventName.CHARGING_COMPLETED,
                data=ServiceEventChargingData(
                    user_id=USER_ID,
                    vin=VIN,
                    mode=None,
                    state=None,
                    soc=None,
                    charged_range=None,
                    time_to_finish=None,
                ),
            ),
        ),
        EventVehicleConnectionStatusUpdate(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=VehicleEvent(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=VehicleEventName.VEHICLE_CONNECTION_ONLINE,
                data=VehicleEventData(
                    user_id=USER_ID,
                    vin=VIN,
                ),
            ),
        ),
        EventVehicleConnectionStatusUpdate(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=VehicleEvent(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=VehicleEventName.VEHICLE_AWAKE,
                data=VehicleEventData(
                    user_id=USER_ID,
                    vin=VIN,
                ),
            ),
        ),
        EventVehicleConnectionStatusUpdate(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=VehicleEvent(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=VehicleEventName.VEHICLE_WARNING_BATTEYLEVEL,
                data=VehicleEventData(
                    user_id=USER_ID,
                    vin=VIN,
                ),
            ),
        ),
        EventVehicleIgnitionStatus(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=VehicleEventWithVehicleIgnitionStatusData(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=VehicleEventName.VEHICLE_IGNITION_STATUS_CHANGED,
                data=VehicleEventVehicleIgnitionStatusData(
                    user_id=USER_ID,
                    vin=VIN,
                    ignition_status=IgnitionStatus.ON,
                ),
            ),
        ),
        EventVehicleIgnitionStatus(
            vin=VIN,
            user_id=USER_ID,
            timestamp=ANY,
            event=VehicleEventWithVehicleIgnitionStatusData(
                version=1,
                trace_id=trace_id,
                timestamp=timestamp,
                producer="SKODA_MHUB",
                name=VehicleEventName.VEHICLE_IGNITION_STATUS_CHANGED,
                data=VehicleEventVehicleIgnitionStatusData(
                    user_id=USER_ID,
                    vin=VIN,
                    ignition_status=IgnitionStatus.OFF,
                ),
            ),
        ),
    ]
