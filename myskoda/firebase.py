"""Firebase helpers used for MQTT authentication.

Todo:
- Create common HTTPClient with make_request(), ... for use here and in rest_api.py
"""

import asyncio
import json
import logging
from os import PathLike
from pathlib import Path
from typing import Any

import aiofiles
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


async def _load_credentials(credentials_file: Path) -> dict[str, Any] | None:
    try:
        async with aiofiles.open(credentials_file, encoding="utf-8") as file_handle:
            contents = await file_handle.read()
    except FileNotFoundError:
        return None
    credentials = json.loads(contents)
    _LOGGER.debug("Loaded Firebase credentials from %s", credentials_file)
    return credentials


async def _save_credentials(credentials_file: Path, credentials: dict[str, Any]) -> None:
    async with aiofiles.open(credentials_file, "w", encoding="utf-8") as file_handle:
        await file_handle.write(json.dumps(credentials))


class FirebaseClient:
    """Handle FCM (Firebase Cloud Messaging) credentials acquisition.

    Args:
        session: aiohttp.ClientSession to use for HTTP requests.
        credentials_file: Optional file path to persist FCM credentials.
    """

    def __init__(
        self, session: aiohttp.ClientSession, credentials_file: str | PathLike[str] | None = None
    ) -> None:
        self._session = session
        self._credentials: dict[str, Any] = {}
        self._credentials_file = Path(credentials_file) if credentials_file else None
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
        self._pending_tasks: set[asyncio.Task] = set()

    async def get_fcm_token(self) -> str:
        """Return a valid FCM token."""
        credentials = (
            await _load_credentials(self._credentials_file) if self._credentials_file else None
        )
        _LOGGER.debug("Checkin or register with FCM")
        async with aiohttp.ClientSession(headers=self._firebase_headers) as firebase_session:
            client = FcmPushClient(
                callback=self._ignore_push_message,
                fcm_config=self._fcm_config,
                credentials=credentials,
                credentials_updated_callback=self._credentials_updated_callback,
                http_client_session=firebase_session,
            )
            return await client.checkin_or_register()

    def _credentials_updated_callback(self, credentials: dict[str, Any]) -> None:
        self._credentials = credentials
        if self._credentials_file:
            _LOGGER.debug("Persisting Firebase credentials to %s", self._credentials_file)
            task = asyncio.ensure_future(_save_credentials(self._credentials_file, credentials))
            self._pending_tasks.add(task)
            task.add_done_callback(self._pending_tasks.discard)

    @staticmethod
    def _ignore_push_message(
        _message: dict[str, object], _token: str, _context: object | None
    ) -> None:
        """Ignore push callbacks while only using the registration flow."""
