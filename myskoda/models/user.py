"""User that is using the API."""

import logging
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import BaseResponse

_LOGGER = logging.getLogger(__name__)


class UserCapabilityId(StrEnum):
    SPIN_MANAGEMENT = "SPIN_MANAGEMENT"
    THIRD_PARTY_OFFERS = "THIRD_PARTY_OFFERS"
    MARKETING_CONSENT = "MARKETING_CONSENT"
    MARKETING_CONSENT_GENERIC = "MARKETING_CONSENT_GENERIC"
    MARKETING_CONSENT_SAD = "MARKETING_CONSENT_SAD"
    MARKETING_CONSENT_SAD_THIRD_PARTY = "MARKETING_CONSENT_SAD_THIRD_PARTY"
    MARKETING_CONSENT_SAD_DEALERS = "MARKETING_CONSENT_SAD_DEALERS"
    TEST_DRIVE = "TEST_DRIVE"


@dataclass
class UserCapability(DataClassORJSONMixin):
    id: UserCapabilityId


def drop_unknown_capabilities(value: list[dict]) -> list[UserCapability]:
    """Drop any unknown usercapabilities and log a message."""
    unknown_capabilities = [c for c in value if c["id"] not in UserCapabilityId]
    if unknown_capabilities:
        _LOGGER.info("Dropping unknown capabilities: %s", unknown_capabilities)
    return [UserCapability.from_dict(c) for c in value if c["id"] in UserCapabilityId]


@dataclass
class User(BaseResponse):
    capabilities: list[UserCapability] = field(
        metadata=field_options(deserialize=drop_unknown_capabilities)
    )
    email: str
    id: str
    last_name: str = field(metadata=field_options(alias="lastName"))
    nickname: str
    preferred_language: str = field(metadata=field_options(alias="preferredLanguage"))
    profile_picture_url: str | None = field(
        default=None, metadata=field_options(alias="profilePictureUrl")
    )
    date_of_birth: date | None = field(default=None, metadata=field_options(alias="dateOfBirth"))
    preferred_contact_channel: str | None = field(
        default=None, metadata=field_options(alias="preferredContactChannel")
    )
    first_name: str | None = field(default=None, metadata=field_options(alias="firstName"))
    phone: str | None = None
    country: str | None = None
