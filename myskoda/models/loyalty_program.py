"""Models for responses of /v2/loyalty-program endpoint."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin
from yarl import URL

from .common import BaseResponse


class URLConfig(BaseConfig):
    serialization_strategy = {  # noqa: RUF012
        URL: {
            "serialize": str,
            "deserialize": URL,
        }
    }


@dataclass
class BaseChallenge(DataClassORJSONMixin):
    name: str
    description: str
    detailed_description: str = field(metadata=field_options(alias="detailedDescription"))
    points: int
    image_url: URL = field(metadata=field_options(alias="imageUrl"))
    total_activities: int = field(metadata=field_options(alias="totalActivities"))
    completed_activities: int = field(metadata=field_options(alias="completedActivities"))

    class Config(URLConfig):
        """Configuration for URL handling."""


class ChallengeType(StrEnum):
    TELEMETRIC = "TELEMETRIC"
    CAR_IN_GARAGE = "CAR_IN_GARAGE"
    PREFERRED_DEALER_SELECTION = "PREFERRED_DEALER_SELECTION"


class ChallengeStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ProgressType(StrEnum):
    NEGATIVE = "NEGATIVE"
    STANDARD = "STANDARD"


@dataclass
class SimpleChallenge(BaseChallenge):
    id: str
    type: ChallengeType
    status: str
    enrollment_required: bool = field(metadata=field_options(alias="enrollmentRequired"))
    highlighted: bool
    display_image: bool = field(metadata=field_options(alias="displayImage"))
    vehicle_name: str | None = field(default=None, metadata=field_options(alias="vehicleName"))
    vin: str | None = field(default=None)
    progress_type: ProgressType | None = field(
        default=None, metadata=field_options(alias="progressType")
    )
    show_eligibility_hint: bool | None = field(
        default=None, metadata=field_options(alias="showEligibilityHint")
    )
    max_failed_attempts: int | None = field(
        default=None, metadata=field_options(alias="maxFailedAttempts")
    )
    attempts_remaining: int | None = field(
        default=None, metadata=field_options(alias="attemptsRemaining")
    )
    days_to_complete: int | None = field(
        default=None, metadata=field_options(alias="daysToComplete")
    )
    days_completed: int | None = field(default=None, metadata=field_options(alias="daysCompleted"))
    ends_at: datetime | None = field(default=None, metadata=field_options(alias="endsAt"))


@dataclass
class InProgressChallenge(SimpleChallenge):
    pass


@dataclass
class ReferralChallenge(BaseChallenge):
    pass


@dataclass
class DailyCheckInChallenge(DataClassORJSONMixin):
    challenge_length: int | None = field(
        default=None, metadata=field_options(alias="challengeLength")
    )
    streak_length: int | None = field(default=None, metadata=field_options(alias="streakLength"))


@dataclass
class LoyaltyProgramMember(BaseResponse):
    point_balance: int | None = field(default=None, metadata=field_options(alias="pointBalance"))
    enrollment_country_code: str | None = field(
        default=None, metadata=field_options(alias="enrollmentCountryCode")
    )
    member_referral_code: str | None = field(
        default=None, metadata=field_options(alias="memberReferralCode")
    )
    daily_check_in_collected: bool | None = field(
        default=None, metadata=field_options(alias="dailyCheckInCollected")
    )
    enrolled_to_loyalty_badges: bool | None = field(
        default=None, metadata=field_options(alias="enrolledToLoyaltyBadges")
    )
    active_rewards: list[Any] | None = field(
        default=None, metadata=field_options(alias="activeRewards")
    )
    consent_required: bool | None = field(
        default=None, metadata=field_options(alias="consentRequired")
    )
    daily_check_in_challenge: DailyCheckInChallenge | None = field(
        default=None, metadata=field_options(alias="dailyCheckInChallenge")
    )
    referral_challenge: ReferralChallenge | None = field(
        default=None, metadata=field_options(alias="referralChallenge")
    )
    in_progress_challenges: list[InProgressChallenge] | None = field(
        default=None, metadata=field_options(alias="inProgressChallenges")
    )


@dataclass
class BadgeBase(DataClassORJSONMixin):
    id: str
    name: str
    description: str
    image: URL

    class Config(URLConfig):
        """Configuration for URL handling."""


@dataclass
class Badge(BadgeBase):
    collected: bool
    weight: float
    collected_at: datetime | None = field(default=None, metadata=field_options(alias="collectedAt"))


@dataclass
class Button(DataClassORJSONMixin):
    title: str | None = field(default=None)
    action: str | None = field(default=None)


class ProgressStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"


@dataclass
class Progress(DataClassORJSONMixin):
    status: ProgressStatus
    progress_in_pct: int = field(metadata=field_options(alias="progressInPct"))
    collected: bool
    collected_at: datetime | None = field(default=None, metadata=field_options(alias="collectedAt"))


class BadgeCategory(StrEnum):
    REFERRAL = "Referral"
    DRIVING = "Driving"
    PROFILE = "Profile"


@dataclass
class BadgeResponse(BaseResponse, BadgeBase):
    disclaimer: str
    category: BadgeCategory
    progress: Progress
    button: Button


@dataclass
class CategoryBadge(DataClassORJSONMixin):
    name: BadgeCategory
    weight: float
    badges: list[Badge]


@dataclass
class BadgesResponse(BaseResponse):
    category_badges: list[CategoryBadge] = field(metadata=field_options(alias="categoryBadges"))


@dataclass
class Challenge(SimpleChallenge):
    completed_at: datetime | None = field(default=None, metadata=field_options(alias="completedAt"))


@dataclass
class ChallengesResponse(BaseResponse):
    challenges: list[Challenge]
    account_point_balance: int = field(metadata=field_options(alias="accountPointBalance"))
    daily_check_in_collected: bool = field(metadata=field_options(alias="dailyCheckInCollected"))
    daily_check_in_challenge: DailyCheckInChallenge | None = field(
        default=None, metadata=field_options(alias="dailyCheckInChallenge")
    )


class VoucherCategory(StrEnum):
    ACCESSORIES = "ACCESSORIES"
    WEBSHOP = "WEBSHOP"


@dataclass
class Voucher(DataClassORJSONMixin):
    id: str
    category: VoucherCategory
    name: str
    description: str
    detailed_description: str = field(metadata=field_options(alias="detailedDescription"))
    terms_and_conditions_url: URL = field(metadata=field_options(alias="termsAndConditionsUrl"))
    points_required: int = field(metadata=field_options(alias="pointsRequired"))
    image_urls: list[URL] = field(metadata=field_options(alias="imageUrls"))
    value: float | None = field(default=None)
    currency: str | None = field(default=None)

    class Config(URLConfig):
        """Configuration for URL handling."""


@dataclass
class RewardResponse(BaseResponse):
    account_point_balance: int = field(metadata=field_options(alias="accountPointBalance"))
    available_rewards: list[Any] = field(metadata=field_options(alias="availableRewards"))
    active_rewards: list[Any] = field(metadata=field_options(alias="activeRewards"))
    redeemed_rewards: list[Any] = field(metadata=field_options(alias="redeemedRewards"))
    available_vouchers: list[Voucher] = field(metadata=field_options(alias="availableVouchers"))
    issued_vouchers: list[Any] = field(metadata=field_options(alias="issuedVouchers"))
    redeemed_vouchers: list[Any] = field(metadata=field_options(alias="redeemedVouchers"))


@dataclass
class LoyaltyProgramDetailsResponse(BaseResponse):
    name: str
    rewards_available: bool = field(metadata=field_options(alias="rewardsAvailable"))


class TransactionType(StrEnum):
    CREDIT = "CREDIT"


@dataclass
class Transaction(DataClassORJSONMixin):
    id: str
    type: TransactionType
    name: str
    points_amount: int = field(metadata=field_options(alias="pointsAmount"))
    timestamp: datetime


@dataclass
class TransactionsResponse(BaseResponse):
    transactions: list[Transaction]


@dataclass
class GamesResponse(BaseResponse):
    games: list[Any]


@dataclass
class SalesforceContactResponse(BaseResponse):
    contact_id: str = field(metadata=field_options(alias="contactId"))
