"""User that is using the API."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class UserCapabilityId(StrEnum):
    SPIN_MANAGEMENT = "SPIN_MANAGEMENT"
    THIRD_PARTY_OFFERS = "THIRD_PARTY_OFFERS"
    MARKETING_CONSENT = "MARKETING_CONSENT"
    TEST_DRIVE = "TEST_DRIVE"


class UserCapability(BaseModel):
    id: UserCapabilityId


class User(BaseModel):
    capabilities: list[UserCapability]
    country: str
    date_of_birth: date = Field(None, alias="dateOfBirth")
    email: str
    first_name: str = Field(None, alias="firstName")
    id: str
    last_name: str = Field(None, alias="lastName")
    nickname: str
    phone: str
    preferred_contact_channel: str = Field(None, alias="preferredContactChannel")
    preferred_language: str = Field(None, alias="preferredLanguage")
    profile_picture_url: str = Field(None, alias="profilePictureUrl")
