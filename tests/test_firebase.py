"""Unit tests for Firebase helpers."""

import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from aiohttp import ClientSession
from firebase_messaging import FcmRegisterConfig
from firebase_messaging.fcmpushclient import CredentialsUpdatedCallable

from myskoda.firebase import FirebaseClient


@pytest.mark.asyncio
async def test_get_fcm_token_loads_and_persists_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    credentials_file = tmp_path / "fcm_credentials.json"
    credentials_file.write_text(json.dumps({"token": "old"}), encoding="utf-8")

    captured: dict[str, object] = {}

    class FakeFcmPushClient:
        def __init__(
            self,
            callback: Callable[[dict, str, Any | None], None],  # noqa: ARG002
            fcm_config: FcmRegisterConfig,  # noqa: ARG002
            credentials: dict | None = None,
            credentials_updated_callback: CredentialsUpdatedCallable | None = None,
            http_client_session: ClientSession | None = None,
        ) -> None:
            captured["credentials"] = credentials
            captured["session"] = http_client_session
            assert credentials_updated_callback is not None
            self._credentials_updated_callback = credentials_updated_callback

        async def checkin_or_register(self) -> str:
            self._credentials_updated_callback({"token": "new"})
            return "fcm-token"

    monkeypatch.setattr("myskoda.firebase.FcmPushClient", FakeFcmPushClient)

    async with ClientSession() as session:
        firebase = FirebaseClient(session, credentials_file=credentials_file)
        token = await firebase.get_fcm_token()
        await asyncio.gather(*firebase._pending_tasks)  # noqa: SLF001

    assert token == "fcm-token"  # noqa: S105
    assert captured["credentials"] == {"token": "old"}
    assert json.loads(credentials_file.read_text(encoding="utf-8")) == {"token": "new"}
