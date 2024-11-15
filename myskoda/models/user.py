"""User that is using the API."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


class UserCapabilityId(StrEnum):
    SPIN_MANAGEMENT = "SPIN_MANAGEMENT"
    THIRD_PARTY_OFFERS = "THIRD_PARTY_OFFERS"
    MARKETING_CONSENT = "MARKETING_CONSENT"
    TEST_DRIVE = "TEST_DRIVE"


@dataclass
class UserCapability(DataClassORJSONMixin):
    id: UserCapabilityId


@dataclass
class User(DataClassORJSONMixin):
    capabilities: list[UserCapability]
    email: str
    first_name: str = field(metadata=field_options(alias="firstName"))
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
    phone: str | None = None
    country: str | None = None
