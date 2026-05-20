"""Firebase helpers used for MQTT authentication.

Todo:
- Create common HTTPClient with make_request(), ... for use here and in rest_api.py
"""

import logging
from typing import Any

import aiohttp
from firebase_messaging import FcmPushClient, FcmRegisterConfig

from .const import (
    FIREBASE_ANDROID_CERT,
    FIREBASE_ANDROID_PACKAGE,
    FIREBASE_API_KEY,
    FIREBASE_APP_ID,
    FIREBASE_PROJECT_ID,
    FIREBASE_SENDER_ID,
)

_LOGGER = logging.getLogger(__name__)


class FirebaseClient:
    """Handle FCM (Firebase Cloud Messaging) credentials acquisition.

    Args:
        session: aiohttp.ClientSession to use for HTTP requests.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._credentials: dict[str, Any] = {}
        self._fcm_config = FcmRegisterConfig(
            FIREBASE_PROJECT_ID,
            FIREBASE_APP_ID,
            FIREBASE_API_KEY,
            FIREBASE_SENDER_ID,
        )
        self._firebase_headers = {
            "X-Android-Package": FIREBASE_ANDROID_PACKAGE,
            "X-Android-Cert": FIREBASE_ANDROID_CERT,
        }

    async def get_fcm_token(self) -> str:
        """Return a valid FCM token."""
        _LOGGER.debug("Checkin or register with FCM")
        async with aiohttp.ClientSession(headers=self._firebase_headers) as firebase_session:
            client = FcmPushClient(
                callback=self._ignore_push_message,
                fcm_config=self._fcm_config,
                credentials_updated_callback=self._credentials_updated_callback,
                http_client_session=firebase_session,
            )
            return await client.checkin_or_register()

    def _credentials_updated_callback(self, credentials: dict[str, Any]) -> None:
        self._credentials = credentials

    @staticmethod
    def _ignore_push_message(
        _message: dict[str, object], _token: str, _context: object | None
    ) -> None:
        """Ignore push callbacks while only using the registration flow."""
