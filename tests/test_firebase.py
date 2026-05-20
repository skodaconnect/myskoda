"""Unit tests for Firebase helpers."""

from collections.abc import Callable
from typing import Any

import pytest
from aiohttp import ClientSession
from firebase_messaging import FcmRegisterConfig
from firebase_messaging.fcmpushclient import CredentialsUpdatedCallable

from myskoda.firebase import FirebaseClient


@pytest.mark.asyncio
async def test_get_fcm_token_loads_and_persists_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
            self._credentials_updated_callback({"fcm": {"token": "fcm-token"}})
            return "fcm-token"

    monkeypatch.setattr("myskoda.firebase.FcmPushClient", FakeFcmPushClient)

    async with ClientSession() as session:
        firebase = FirebaseClient(session)
        token = await firebase.get_fcm_token()

    assert token == "fcm-token"  # noqa: S105
    assert firebase._credentials["fcm"]["token"] == "fcm-token"  # noqa: SLF001, S105
