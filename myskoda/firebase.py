"""Firebase helpers used for MQTT authentication.

Todo:
- Create common HTTPClient with make_request(), ... for use here and in rest_api.py
"""

import asyncio
import gzip
import hashlib
import json
import logging
import uuid
from base64 import urlsafe_b64encode
from typing import Any

import aiohttp
from firebase_messaging import FcmRegisterConfig
from firebase_messaging.const import AUTH_VERSION, FCM_INSTALLATION, GCM_REGISTER_URL
from firebase_messaging.fcmregister import FcmRegister

from .const import (
    FIREBASE_ANDROID_CERT,
    FIREBASE_ANDROID_FCM_CLIENT_VERSION,
    FIREBASE_ANDROID_FIS_SDK_VERSION,
    FIREBASE_ANDROID_OS_VERSION,
    FIREBASE_ANDROID_PACKAGE,
    FIREBASE_API_KEY,
    FIREBASE_APP_ID,
    FIREBASE_GMS_VERSION,
    FIREBASE_PROJECT_ID,
    FIREBASE_REGISTER_DEFAULT_RETRIES,
    FIREBASE_SENDER_ID,
    MYSKODA_APP_VERSION,
    MYSKODA_APP_VERSION_CODE,
)

_LOGGER = logging.getLogger(__name__)


class FirebaseClient:
    """Handle FCM (Firebase Cloud Messaging) credentials acquisition."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._fcm_config = FcmRegisterConfig(
            FIREBASE_PROJECT_ID,
            FIREBASE_APP_ID,
            FIREBASE_API_KEY,
            FIREBASE_SENDER_ID,
        )
        self._firebase_headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Encoding": "gzip",
            "Content-Type": "application/json",
            "X-Android-Cert": FIREBASE_ANDROID_CERT,
            "X-Android-Package": FIREBASE_ANDROID_PACKAGE,
            "x-goog-api-key": FIREBASE_API_KEY,
        }

    async def get_fcm_token(self) -> str:
        """Return a valid FCM token."""
        _LOGGER.debug("Checkin and register with Android FCM")
        gcm_credentials = await self._get_gcm_credentials()
        installation = await self._install_firebase()
        return await self._register_android_fcm_token(gcm_credentials, installation)

    async def _get_gcm_credentials(self) -> dict[str, Any]:
        register = FcmRegister(
            self._fcm_config,
            http_client_session=self._session,
        )
        try:
            credentials = await register.gcm_check_in()
        finally:
            await register.close()

        if credentials is None:
            msg = "Unable to check in with Google Cloud Messaging."
            raise RuntimeError(msg)
        return credentials

    async def _install_firebase(self) -> dict[str, Any]:
        fid = self._generate_fid()
        payload = {
            "fid": fid,
            "appId": FIREBASE_APP_ID,
            "authVersion": AUTH_VERSION,
            "sdkVersion": FIREBASE_ANDROID_FIS_SDK_VERSION,
        }
        url = f"{FCM_INSTALLATION}projects/{FIREBASE_PROJECT_ID}/installations"
        async with self._session.post(
            url=url,
            headers=self._firebase_headers,
            data=gzip.compress(json.dumps(payload).encode("utf-8")),
        ) as response:
            response.raise_for_status()
            installation = await response.json()

        return {
            "fid": installation["fid"],
            "auth_token": installation["authToken"]["token"],
        }

    async def _register_android_fcm_token(
        self,
        gcm_credentials: dict[str, Any],
        installation: dict[str, Any],
        retries: int = FIREBASE_REGISTER_DEFAULT_RETRIES,
    ) -> str:
        android_id = str(gcm_credentials["androidId"])
        security_token = str(gcm_credentials["securityToken"])
        data = {
            "app": FIREBASE_ANDROID_PACKAGE,
            "cert": FIREBASE_ANDROID_CERT,
            "device": android_id,
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
            "firebase-app-name-hash": self._firebase_app_name_hash(),
            "X-Goog-Firebase-Installations-Auth": installation["auth_token"],
            "appid": installation["fid"],
            "cliv": FIREBASE_ANDROID_FCM_CLIENT_VERSION,
        }

        for attempt in range(1, retries + 1):
            async with self._session.post(
                url=GCM_REGISTER_URL,
                headers={
                    "Authorization": f"AidLogin {android_id}:{security_token}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=data,
            ) as response:
                response_text = await response.text()
                response.raise_for_status()

            if not response_text.startswith("Error=") or attempt == retries:
                return self._parse_gcm_register_response(response_text)

            _LOGGER.debug(
                "Retrying Android FCM registration after %s (%s/%s)",
                response_text,
                attempt,
                retries,
            )
            await asyncio.sleep(1)

        msg = "Unable to register with Android FCM."
        raise RuntimeError(msg)

    @staticmethod
    def _generate_fid() -> str:
        uuid_bytes = bytearray(uuid.uuid4().bytes)
        fid_bytes = uuid_bytes + uuid_bytes[:1]
        fid_bytes[0] = (fid_bytes[0] & 0x0F) | 0x70
        return urlsafe_b64encode(fid_bytes).decode("ascii").rstrip("=")[:22]

    @staticmethod
    def _firebase_app_name_hash() -> str:
        digest = hashlib.sha1(b"[DEFAULT]").digest()  # noqa: S324
        return urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    @staticmethod
    def _parse_gcm_register_response(response_text: str) -> str:
        key, separator, value = response_text.partition("=")
        if separator and key == "token" and value:
            return value

        msg = f"Unable to register with Android FCM: {response_text}"
        raise RuntimeError(msg)
