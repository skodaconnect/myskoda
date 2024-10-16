"""Unit tests for MQTT."""

from pathlib import Path
from socket import socket

import pytest
from amqtt.client import QOS_2, MQTTClient

from myskoda.anonymize import VIN
from myskoda.models.operation_request import OperationName
from myskoda.myskoda import MySkoda

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def random_port() -> int:
    with socket() as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


@pytest.mark.asyncio
async def test_wait_for_operation(
    mqtt_client: MQTTClient,
    myskoda: MySkoda,
) -> None:
    if myskoda.mqtt is None:
        return

    topic = f"b8bc126c-ee36-402b-8723-2c1c3dff8dec/{VIN}/operation-request/air-conditioning/start-stop-air-conditioning"  # noqa: E501

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
