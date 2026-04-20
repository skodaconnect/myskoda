"""Firebase helpers used for MQTT authentication.

Todo:
- Create common HTTPClient with make_request(), ... for use here and in rest_api.py
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import aiohttp
from filelock import AsyncFileLock
from firebase_messaging import FcmPushClient, FcmRegisterConfig

from .const import (
    DEFAULT_FCM_CREDENTIALS_FILE,
    FIREBASE_ANDROID_CERT,
    FIREBASE_ANDROID_PACKAGE,
    FIREBASE_API_KEY,
    FIREBASE_APP_ID,
    FIREBASE_PROJECT_ID,
    FIREBASE_SENDER_ID,
)

_LOGGER = logging.getLogger(__name__)


def _default_credentials_path() -> Path:
    return Path.cwd() / DEFAULT_FCM_CREDENTIALS_FILE


def _load_credentials(credentials_file: Path) -> dict[str, Any] | None:
    if not credentials_file.exists():
        return None
    with credentials_file.open(encoding="utf-8") as file_handle:
        return json.load(file_handle)


def _save_credentials(credentials_file: Path, credentials: dict[str, Any]) -> None:
    with credentials_file.open("w", encoding="utf-8") as file_handle:
        json.dump(credentials, file_handle)


class FirebaseClient:
    """Handle FCM (Firebase Cloud Messaging) token acquisition and registration."""

    def __init__(
        self, session: aiohttp.ClientSession, credentials_file: str | os.PathLike[str] | None = None
    ) -> None:
        self._session = session
        self._credentials_file = (
            Path(credentials_file) if credentials_file else _default_credentials_path()
        )
        self._credentials_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = AsyncFileLock(f"{self._credentials_file}.lock")
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
        """Return a valid FCM token, persisting updated credentials when needed."""
        async with self._lock:
            credentials = _load_credentials(self._credentials_file)
            async with aiohttp.ClientSession(headers=self._firebase_headers) as firebase_session:
                client = FcmPushClient(
                    callback=self._ignore_push_message,
                    fcm_config=self._fcm_config,
                    credentials=credentials,
                    credentials_updated_callback=self._persist_credentials,
                    http_client_session=firebase_session,
                )
                return await client.checkin_or_register()

    def _persist_credentials(self, credentials: dict[str, Any]) -> None:
        _LOGGER.debug("Persisting Firebase credentials to %s", self._credentials_file)
        _save_credentials(self._credentials_file, credentials)

    @staticmethod
    def _ignore_push_message(
        _message: dict[str, object], _token: str, _context: object | None
    ) -> None:
        """Ignore push callbacks while only using the registration flow."""
