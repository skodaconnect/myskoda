"""User that is using the API."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.json import DataClassJSONMixin


class UserCapabilityId(StrEnum):
    SPIN_MANAGEMENT = "SPIN_MANAGEMENT"
    THIRD_PARTY_OFFERS = "THIRD_PARTY_OFFERS"
    MARKETING_CONSENT = "MARKETING_CONSENT"
    TEST_DRIVE = "TEST_DRIVE"


@dataclass
class UserCapability(DataClassJSONMixin):
    id: UserCapabilityId


@dataclass
class User(DataClassJSONMixin):
    capabilities: list[UserCapability]
    country: str
    date_of_birth: date = field(metadata=field_options(alias="dateOfBirth"))
    email: str
    first_name: str = field(metadata=field_options(alias="firstName"))
    id: str
    last_name: str = field(metadata=field_options(alias="lastName"))
    nickname: str
    phone: str
    preferred_contact_channel: str = field(metadata=field_options(alias="preferredContactChannel"))
    preferred_language: str = field(metadata=field_options(alias="preferredLanguage"))
    profile_picture_url: str = field(metadata=field_options(alias="profilePictureUrl"))
