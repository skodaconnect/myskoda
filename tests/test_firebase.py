"""Unit tests for Firebase helpers."""

import gzip
import json
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses
from firebase_messaging.const import AUTH_VERSION, FCM_INSTALLATION, GCM_REGISTER_URL

from myskoda.const import (
    FIREBASE_ANDROID_CERT,
    FIREBASE_ANDROID_FCM_CLIENT_VERSION,
    FIREBASE_ANDROID_FIS_SDK_VERSION,
    FIREBASE_ANDROID_OS_VERSION,
    FIREBASE_ANDROID_PACKAGE,
    FIREBASE_API_KEY,
    FIREBASE_APP_ID,
    FIREBASE_GMS_VERSION,
    FIREBASE_PROJECT_ID,
    FIREBASE_SENDER_ID,
    MYSKODA_APP_VERSION,
    MYSKODA_APP_VERSION_CODE,
)
from myskoda.firebase import FirebaseClient


@pytest.mark.asyncio
async def test_get_fcm_token_uses_android_registration(
    monkeypatch: pytest.MonkeyPatch, responses: aioresponses
) -> None:
    fis_url = f"{FCM_INSTALLATION}projects/{FIREBASE_PROJECT_ID}/installations"
    captured_sessions: dict[str, ClientSession] = {}

    async def fake_get_gcm_credentials(_client: FirebaseClient) -> dict[str, str]:
        captured_sessions["firebase"] = _client._session  # noqa: SLF001
        return {"androidId": "android-id", "securityToken": "security-token"}

    monkeypatch.setattr(FirebaseClient, "_get_gcm_credentials", fake_get_gcm_credentials)
    monkeypatch.setattr(FirebaseClient, "_generate_fid", staticmethod(lambda: "fid"))
    responses.post(
        fis_url,
        payload={
            "fid": "fid",
            "refreshToken": "refresh-token",
            "authToken": {"token": "fis-auth-token", "expiresIn": "604800s"},
        },
    )
    responses.post(GCM_REGISTER_URL, body="token=android-fcm-token")

    async with ClientSession() as parent_session:
        firebase = FirebaseClient(parent_session)
        token = await firebase.get_fcm_token()
        assert captured_sessions["firebase"] is parent_session
        assert not captured_sessions["firebase"].closed

    assert token == "android-fcm-token"  # noqa: S105

    request_calls = iter(responses.requests.values())
    fis_call = next(request_calls)[0]
    fis_payload = json.loads(gzip.decompress(fis_call.kwargs["data"]).decode("utf-8"))
    assert fis_payload == {
        "fid": "fid",
        "appId": FIREBASE_APP_ID,
        "authVersion": AUTH_VERSION,
        "sdkVersion": FIREBASE_ANDROID_FIS_SDK_VERSION,
    }
    assert fis_call.kwargs["headers"] == {
        "X-Android-Package": FIREBASE_ANDROID_PACKAGE,
        "X-Android-Cert": FIREBASE_ANDROID_CERT,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Encoding": "gzip",
        "Cache-Control": "no-cache",
        "x-goog-api-key": FIREBASE_API_KEY,
    }

    register_call = next(request_calls)[0]
    assert register_call.kwargs["headers"] == {
        "Authorization": "AidLogin android-id:security-token",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    assert register_call.kwargs["data"] == {
        "app": FIREBASE_ANDROID_PACKAGE,
        "cert": FIREBASE_ANDROID_CERT,
        "device": "android-id",
        "sender": FIREBASE_SENDER_ID,
        "subtype": FIREBASE_SENDER_ID,
        "X-subtype": FIREBASE_SENDER_ID,
        "scope": "*",
        "X-scope": "*",
        "gmp_app_id": FIREBASE_APP_ID,
        "gmsv": FIREBASE_GMS_VERSION,
        "osv": FIREBASE_ANDROID_OS_VERSION,
        "app_ver": MYSKODA_APP_VERSION_CODE,
        "app_ver_name": MYSKODA_APP_VERSION,
        "firebase-app-name-hash": "R1dAH9Ui7M-ynoznwBdw01tLxhI",
        "X-Goog-Firebase-Installations-Auth": "fis-auth-token",
        "appid": "fid",
        "cliv": FIREBASE_ANDROID_FCM_CLIENT_VERSION,
    }


@pytest.mark.asyncio
async def test_register_android_fcm_token_retries_registration_error(
    monkeypatch: pytest.MonkeyPatch, responses: aioresponses
) -> None:
    sleep = AsyncMock()
    monkeypatch.setattr("myskoda.firebase.asyncio.sleep", sleep)
    responses.post(GCM_REGISTER_URL, body="Error=PHONE_REGISTRATION_ERROR")
    responses.post(GCM_REGISTER_URL, body="token=android-fcm-token")

    async with ClientSession() as session:
        firebase = FirebaseClient(session)
        token = await firebase._register_android_fcm_token(  # noqa: SLF001
            {"androidId": "android-id", "securityToken": "security-token"},
            {"auth_token": "fis-auth-token", "fid": "fid"},
            retries=2,
        )

    assert token == "android-fcm-token"  # noqa: S105
    sleep.assert_awaited_once_with(1)
