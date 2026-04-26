import json
from collections.abc import Callable
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from aioresponses import aioresponses
from yarl import URL

from myskoda.anonymize import VEHICLE_NAME, VIN
from myskoda.models.loyalty_program import (
    DailyCheckInChallenge,
    InProgressChallenge,
    ReferralChallenge,
)
from myskoda.myskoda import MySkoda

FIXTURES_DIR = Path(__file__).parent.joinpath("fixtures")

print(f"__file__ = {__file__}")


DEFAULT_USER_ID = "u12345"


def mock_user_response(user_id: str, responses: aioresponses) -> str:
    """Mock user response for loyalty program badge tests."""
    user = f"""
    {{"id":"{user_id}","email":"john.doe@example.com","firstName":"John","lastName":"Doe","capabilities":[],"preferredLanguage":"en"}}
    """

    responses.get(
        url="https://mysmob.api.connect.skoda-auto.cz/api/v1/users",
        body=user,
    )
    return user_id


async def prepare_user_response_mock(
    responses: aioresponses,
    user_id: str,
    user_response_mock: Callable[[str, aioresponses], str] | None,
) -> str | None:
    real_user_id = None if user_response_mock is not None else user_id
    user_response_mock(user_id, responses) if user_response_mock else None
    return real_user_id


@pytest.fixture(name="badge")
def load_badge() -> list[str]:
    """Load badge fixture."""
    badge = []
    for path in [
        "loyalty_program/loyalty-badge.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            badge.append(file.read())
    return badge


async def load_badge_test(
    badge: list[str],
    myskoda: MySkoda,
    responses: aioresponses,
    mock_user_response_func: Callable[[str, aioresponses], str] | None = None,
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    for badge_input in badge:
        badge_json = json.loads(badge_input)

        badge_id = "12345"
        user_id = await prepare_user_response_mock(
            responses, DEFAULT_USER_ID, mock_user_response_func
        )
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/loyalty-program/members/{DEFAULT_USER_ID}/badges/{badge_id}",
            body=badge_input,
        )
        get_badge_result = await myskoda.get_loyalty_program_badge(badge_id, user_id=user_id)
        # Add assertions for vehicle renders result

        assert get_badge_result.id == badge_json["id"]
        assert get_badge_result.name == badge_json["name"]
        assert get_badge_result.description == badge_json["description"]
        assert get_badge_result.disclaimer == badge_json["disclaimer"]
        assert get_badge_result.category == badge_json["category"]
        assert get_badge_result.button.action == badge_json["button"]["action"]
        assert get_badge_result.button.title == badge_json["button"]["title"]
        assert get_badge_result.image == URL(badge_json["image"])
        assert get_badge_result.progress.collected == badge_json["progress"]["collected"]
        assert get_badge_result.progress.status == badge_json["progress"]["status"]
        assert get_badge_result.progress.progress_in_pct == badge_json["progress"]["progressInPct"]
        assert get_badge_result.progress.collected_at == datetime.fromisoformat(
            badge_json["progress"]["collectedAt"]
        )


@pytest.mark.asyncio
async def test_load_badge_no_user_id(
    badge: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_badge_test(badge, myskoda, responses, mock_user_response_func=mock_user_response)


@pytest.mark.asyncio
async def test_load_badge_with_user_id(
    badge: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_badge_test(badge, myskoda, responses, mock_user_response_func=None)


@pytest.fixture(name="badges")
def load_badges() -> list[str]:
    """Load badge fixture."""
    badges = []
    for path in [
        "loyalty_program/loyalty-badges.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            badges.append(file.read())
    return badges


@pytest.mark.asyncio
async def test_load_badges_no_user_id(
    badges: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_badges_test(badges, myskoda, responses, mock_user_response_func=mock_user_response)


@pytest.mark.asyncio
async def test_load_badges_with_user_id(
    badges: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_badges_test(badges, myskoda, responses, mock_user_response_func=None)


@pytest.mark.asyncio
async def test_load_badges_with_user_id_anonymize(
    badges: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_badges_test(
        badges, myskoda, responses, anonymized=True, mock_user_response_func=None
    )


async def load_badges_test(
    badges: list[str],
    myskoda: MySkoda,
    responses: aioresponses,
    anonymized: bool = False,
    mock_user_response_func: Callable[[str, aioresponses], str] | None = None,
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    for badges_input in badges:
        badges_json = json.loads(badges_input)

        user_id = await prepare_user_response_mock(
            responses, DEFAULT_USER_ID, mock_user_response_func
        )
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/loyalty-program/members/{DEFAULT_USER_ID}/badges",
            body=badges_input,
        )
        get_badges_result = await myskoda.get_loyalty_program_badges(
            user_id=user_id, anonymize=anonymized
        )
        # Add assertions for vehicle renders result

        assert get_badges_result is not None
        category_badges = get_badges_result.category_badges
        assert category_badges is not None
        category_badges_json = badges_json["categoryBadges"]
        assert len(category_badges) == len(category_badges_json)
        for i in range(len(category_badges)):
            category_bade = category_badges[i]
            category_badge_json = category_badges_json[i]
            assert category_bade.name == category_badge_json["name"]
            assert category_bade.weight == category_badge_json["weight"]
            assert category_bade.badges is not None
            badges_for_category = category_bade.badges
            badges_json_for_category = category_badge_json["badges"]
            assert len(badges_for_category) == len(badges_json_for_category)
            for j in range(len(badges_for_category)):
                badge = badges_for_category[j]
                badge_json = badges_json_for_category[j]
                if anonymized:
                    assert badge.id == sha256(badge_json["id"].encode()).hexdigest()
                else:
                    assert badge.id == badge_json["id"]
                assert badge.name == badge_json["name"]
                assert badge.description == badge_json["description"]
                assert badge.image == URL(badge_json["image"])
                assert badge.collected == badge_json["collected"]
                if badge.collected:
                    assert badge.collected_at == datetime.fromisoformat(badge_json["collectedAt"])


@pytest.fixture(name="challenges")
def load_challenges() -> list[str]:
    """Load challenge fixture."""
    challenges = []
    for path in [
        "loyalty_program/loyalty-challenges.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            challenges.append(file.read())
    return challenges


@pytest.mark.asyncio
async def test_load_challenges_no_user_id(
    challenges: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_challenges()."""
    await load_challenges_test(
        challenges, myskoda, responses, mock_user_response_func=mock_user_response
    )


@pytest.mark.asyncio
async def test_load_challenges_with_user_id(
    challenges: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_challenges_test(challenges, myskoda, responses, mock_user_response_func=None)


@pytest.mark.asyncio
async def test_load_challenges_with_user_id_anonymize(
    challenges: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_challenges_test(
        challenges, myskoda, responses, anonymized=True, mock_user_response_func=None
    )


async def load_challenges_test(
    challenges: list[str],
    myskoda: MySkoda,
    responses: aioresponses,
    anonymized: bool = False,
    mock_user_response_func: Callable[[str, aioresponses], str] | None = None,
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    for challenges_input in challenges:
        challenges_json = json.loads(challenges_input)

        user_id = await prepare_user_response_mock(
            responses, DEFAULT_USER_ID, mock_user_response_func
        )
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/loyalty-program/members/{DEFAULT_USER_ID}/challenges",
            body=challenges_input,
        )
        get_challenges_result = await myskoda.get_loyalty_program_challenges(
            user_id=user_id, anonymize=anonymized
        )
        # Add assertions for vehicle renders result

        assert get_challenges_result is not None
        assert get_challenges_result.account_point_balance == challenges_json["accountPointBalance"]
        assert (
            get_challenges_result.daily_check_in_collected
            == challenges_json["dailyCheckInCollected"]
        )

        assert get_challenges_result.daily_check_in_challenge is not None
        assert (
            get_challenges_result.daily_check_in_challenge.challenge_length
            == challenges_json["dailyCheckInChallenge"]["challengeLength"]
        )
        assert (
            get_challenges_result.daily_check_in_challenge.streak_length
            == challenges_json["dailyCheckInChallenge"]["streakLength"]
        )
        assert get_challenges_result.challenges is not None
        challenges_list = get_challenges_result.challenges
        challenges_list_json = challenges_json["challenges"]
        assert len(challenges_list) == len(challenges_list_json)
        for i in range(len(challenges_list)):
            challenge = challenges_list[i]
            challenge_json = challenges_list_json[i]
            assert challenge.type == challenge_json["type"]
            assert challenge.status == challenge_json["status"]
            assert challenge.enrollment_required == challenge_json["enrollmentRequired"]
            assert challenge.name == challenge_json["name"]
            assert challenge.description == challenge_json["description"]
            assert challenge.detailed_description == challenge_json["detailedDescription"]
            assert challenge.points == challenge_json["points"]
            assert challenge.image_url == URL(challenge_json["imageUrl"])
            assert challenge.highlighted == challenge_json["highlighted"]
            assert (
                challenge.ends_at == datetime.fromisoformat(challenge_json["endsAt"])
                if "endsAt" in challenge_json
                else challenge.ends_at is None
            )
            assert challenge.total_activities == challenge_json["totalActivities"]
            assert challenge.completed_activities == challenge_json["completedActivities"]
            if "vin" in challenge_json:
                if anonymized:
                    assert challenge.id == sha256(challenge_json["id"].encode()).hexdigest()
                    assert challenge.vin == VIN
                    assert challenge.vehicle_name == VEHICLE_NAME
                else:
                    assert challenge.id == challenge_json["id"]
                    assert challenge.vin == challenge_json["vin"]
                    assert challenge.vehicle_name == challenge_json["vehicleName"]
            assert (
                challenge.show_eligibility_hint == challenge_json["showEligibilityHint"]
                if "showEligibilityHint" in challenge_json
                else challenge.show_eligibility_hint is None
            )
            assert (
                challenge.progress_type == challenge_json["progressType"]
                if "progressType" in challenge_json
                else challenge.progress_type is None
            )
            assert (
                challenge.max_failed_attempts == challenge_json["maxFailedAttempts"]
                if "maxFailedAttempts" in challenge_json
                else challenge.max_failed_attempts is None
            )
            assert (
                challenge.attempts_remaining == challenge_json["attemptsRemaining"]
                if "attemptsRemaining" in challenge_json
                else challenge.attempts_remaining is None
            )
            assert (
                challenge.days_to_complete == challenge_json["daysToComplete"]
                if "daysToComplete" in challenge_json
                else challenge.days_to_complete is None
            )
            assert (
                challenge.days_completed == challenge_json["daysCompleted"]
                if "daysCompleted" in challenge_json
                else challenge.days_completed is None
            )


@pytest.fixture(name="details")
def load_details() -> list[str]:
    """Load details fixture."""
    details = []
    for path in [
        "loyalty_program/loyalty-details.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            details.append(file.read())
    return details


async def test_load_details(details: list[str], myskoda: MySkoda, responses: aioresponses) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    for details_input in details:
        details_json = json.loads(details_input)

        responses.get(
            url="https://mysmob.api.connect.skoda-auto.cz/api/v2/loyalty-program/details",
            body=details_input,
        )
        get_details_result = await myskoda.get_loyalty_program_details()
        # Add assertions for vehicle renders result

        assert get_details_result is not None
        assert get_details_result.name == details_json["name"]
        assert get_details_result.rewards_available == details_json["rewardsAvailable"]


@pytest.fixture(name="loyalty_program_games")
def load_loyalty_program_games() -> list[str]:
    """Load loyalty program games fixture."""
    games = []
    for path in [
        "loyalty_program/loyalty-games.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            games.append(file.read())
    return games


@pytest.mark.asyncio
async def test_load_games_no_user_id(
    loyalty_program_games: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_games_test(
        loyalty_program_games, myskoda, responses, mock_user_response_func=mock_user_response
    )


@pytest.mark.asyncio
async def test_load_games_with_user_id(
    loyalty_program_games: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_games_test(
        loyalty_program_games, myskoda, responses, mock_user_response_func=None
    )


async def load_loyalty_program_games_test(
    games: list[str],
    myskoda: MySkoda,
    responses: aioresponses,
    mock_user_response_func: Callable[[str, aioresponses], str] | None = None,
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    for games_input in games:
        games_json = json.loads(games_input)

        user_id = await prepare_user_response_mock(
            responses, DEFAULT_USER_ID, mock_user_response_func
        )
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/loyalty-program/members/{DEFAULT_USER_ID}/games",
            body=games_input,
        )
        get_details_result = await myskoda.get_loyalty_program_games(user_id=user_id)
        # Add assertions for vehicle renders result

        assert get_details_result is not None
        assert get_details_result.games == games_json["games"]


@pytest.fixture(name="loyalty_program_members")
def load_loyalty_program_members() -> list[str]:
    """Load loyalty program members fixture."""
    members = []
    for path in [
        "loyalty_program/loyalty-member.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            members.append(file.read())
    return members


@pytest.mark.asyncio
async def test_load_members_no_user_id(
    loyalty_program_members: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_members_test(
        loyalty_program_members, myskoda, responses, mock_user_response_func=mock_user_response
    )


@pytest.mark.asyncio
async def test_load_members_with_user_id(
    loyalty_program_members: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_members_test(
        loyalty_program_members, myskoda, responses, mock_user_response_func=None
    )


@pytest.mark.asyncio
async def test_load_members_with_user_id_anonymize(
    loyalty_program_members: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_members_test(
        loyalty_program_members, myskoda, responses, anonymized=True, mock_user_response_func=None
    )


def assert_daily_check_in_challenge(
    result: DailyCheckInChallenge | None, expected_json: dict[str, Any]
) -> None:
    assert result is not None
    assert result.challenge_length == expected_json["challengeLength"]
    assert result.streak_length == expected_json["streakLength"]


def assert_referral_challenge(
    result: ReferralChallenge | None, expected_json: dict[str, Any]
) -> None:
    assert result is not None
    assert result.name == expected_json["name"]
    assert result.description == expected_json["description"]
    assert result.detailed_description == expected_json["detailedDescription"]
    assert result.points == expected_json["points"]
    assert result.image_url == URL(expected_json["imageUrl"])
    assert result.total_activities == expected_json["totalActivities"]
    assert result.completed_activities == expected_json["completedActivities"]


def assert_in_progress_challenge(
    challenge: InProgressChallenge, challenge_json: dict[str, Any], anonymized: bool
) -> None:
    assert challenge.type == challenge_json["type"]
    assert challenge.status == challenge_json["status"]
    assert challenge.enrollment_required == challenge_json["enrollmentRequired"]
    assert challenge.name == challenge_json["name"]
    assert challenge.description == challenge_json["description"]
    assert challenge.detailed_description == challenge_json["detailedDescription"]
    assert challenge.points == challenge_json["points"]
    assert challenge.highlighted == challenge_json["highlighted"]
    assert challenge.image_url == URL(challenge_json["imageUrl"])
    assert challenge.ends_at == datetime.fromisoformat(challenge_json["endsAt"])
    assert challenge.total_activities == challenge_json["totalActivities"]
    assert challenge.completed_activities == challenge_json["completedActivities"]
    if anonymized:
        assert challenge.id == sha256(challenge_json["id"].encode()).hexdigest()
        assert challenge.vin == VIN
        assert challenge.vehicle_name == VEHICLE_NAME
    else:
        assert challenge.id == challenge_json["id"]
        assert challenge.vin == challenge_json["vin"]
        assert challenge.vehicle_name == challenge_json["vehicleName"]
    assert challenge.show_eligibility_hint == challenge_json["showEligibilityHint"]
    assert challenge.progress_type == challenge_json["progressType"]
    assert challenge.max_failed_attempts == challenge_json["maxFailedAttempts"]
    assert challenge.attempts_remaining == challenge_json["attemptsRemaining"]
    assert challenge.days_to_complete == challenge_json["daysToComplete"]
    assert challenge.days_completed == challenge_json["daysCompleted"]


async def load_loyalty_program_members_test(
    members: list[str],
    myskoda: MySkoda,
    responses: aioresponses,
    anonymized: bool = False,
    mock_user_response_func: Callable[[str, aioresponses], str] | None = None,
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    for members_input in members:
        members_json = json.loads(members_input)

        user_id = await prepare_user_response_mock(
            responses, DEFAULT_USER_ID, mock_user_response_func
        )
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/loyalty-program/members/{DEFAULT_USER_ID}",
            body=members_input,
        )
        get_members_result = await myskoda.get_loyalty_program_member(
            user_id=user_id, anonymize=anonymized
        )
        # Add assertions for vehicle renders result

        assert get_members_result is not None
        assert get_members_result.point_balance == members_json["pointBalance"]
        assert get_members_result.enrollment_country_code == members_json["enrollmentCountryCode"]
        if anonymized:
            assert (
                get_members_result.member_referral_code
                == sha256(members_json["memberReferralCode"].encode()).hexdigest()
            )
        else:
            assert get_members_result.member_referral_code == members_json["memberReferralCode"]
        assert get_members_result.daily_check_in_collected == members_json["dailyCheckInCollected"]
        assert (
            get_members_result.enrolled_to_loyalty_badges == members_json["enrolledToLoyaltyBadges"]
        )
        assert get_members_result.active_rewards == members_json["activeRewards"]
        assert get_members_result.consent_required == members_json["consentRequired"]

        assert_daily_check_in_challenge(
            get_members_result.daily_check_in_challenge, members_json["dailyCheckInChallenge"]
        )
        assert_referral_challenge(
            get_members_result.referral_challenge, members_json["referralChallenge"]
        )

        assert get_members_result.in_progress_challenges is not None
        for i in range(len(get_members_result.in_progress_challenges)):
            in_progress_challenge = get_members_result.in_progress_challenges[i]
            in_progress_challenge_json = members_json["inProgressChallenges"][i]
            assert_in_progress_challenge(
                in_progress_challenge, in_progress_challenge_json, anonymized
            )


@pytest.fixture(name="loyalty_program_rewards")
def load_loyalty_program_rewards() -> list[str]:
    """Load loyalty program rewards fixture."""
    rewards = []
    for path in [
        "loyalty_program/loyalty-rewards.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            rewards.append(file.read())
    return rewards


@pytest.mark.asyncio
async def test_load_rewards_no_user_id(
    loyalty_program_rewards: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_rewards_test(
        loyalty_program_rewards, myskoda, responses, mock_user_response_func=mock_user_response
    )


@pytest.mark.asyncio
async def test_load_rewards_with_user_id(
    loyalty_program_rewards: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_rewards_test(
        loyalty_program_rewards, myskoda, responses, mock_user_response_func=None
    )


@pytest.mark.asyncio
async def test_load_rewards_with_user_id_anonymize(
    loyalty_program_rewards: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_rewards_test(
        loyalty_program_rewards, myskoda, responses, anonymized=True, mock_user_response_func=None
    )


async def load_loyalty_program_rewards_test(
    rewards: list[str],
    myskoda: MySkoda,
    responses: aioresponses,
    anonymized: bool = False,
    mock_user_response_func: Callable[[str, aioresponses], str] | None = None,
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    for rewards_input in rewards:
        rewards_json = json.loads(rewards_input)

        user_id = await prepare_user_response_mock(
            responses, DEFAULT_USER_ID, mock_user_response_func
        )
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/loyalty-program/members/{DEFAULT_USER_ID}/rewards",
            body=rewards_input,
        )
        get_rewards_result = await myskoda.get_loyalty_program_rewards(
            user_id=user_id, anonymize=anonymized
        )
        # Add assertions for vehicle renders result

        assert get_rewards_result is not None
        assert get_rewards_result.account_point_balance == rewards_json["accountPointBalance"]
        assert get_rewards_result.available_rewards == rewards_json["availableRewards"]
        assert get_rewards_result.active_rewards == rewards_json["activeRewards"]
        assert get_rewards_result.redeemed_rewards == rewards_json["redeemedRewards"]
        assert get_rewards_result.issued_vouchers == rewards_json["issuedVouchers"]
        assert get_rewards_result.redeemed_vouchers == rewards_json["redeemedVouchers"]

        available_vouchers = get_rewards_result.available_vouchers
        available_vouchers_json = rewards_json["availableVouchers"]
        assert len(available_vouchers) == len(available_vouchers_json)
        for i in range(len(available_vouchers)):
            voucher = available_vouchers[i]
            voucher_json = available_vouchers_json[i]
            if anonymized:
                assert voucher.id == sha256(voucher_json["id"].encode()).hexdigest()
            else:
                assert voucher.id == voucher_json["id"]
            assert voucher.category == voucher_json["category"]
            assert voucher.name == voucher_json["name"]
            assert voucher.description == voucher_json["description"]
            assert voucher.detailed_description == voucher_json["detailedDescription"]
            assert voucher.terms_and_conditions_url == URL(voucher_json["termsAndConditionsUrl"])
            assert voucher.points_required == voucher_json["pointsRequired"]

            if "value" in voucher_json:
                assert voucher.value == voucher_json["value"]
            else:
                assert voucher.value is None

            if "currency" in voucher_json:
                assert voucher.currency == voucher_json["currency"]
            else:
                assert voucher.currency is None

            image_urls = voucher.image_urls
            image_urls_json = voucher_json["imageUrls"]
            assert len(image_urls) == len(image_urls_json)
            for j in range(len(image_urls)):
                assert image_urls[j] == URL(image_urls_json[j])


@pytest.fixture(name="loyalty_program_salesforce")
def load_loyalty_program_salesforce() -> list[str]:
    """Load loyalty program salesforce fixture."""
    salesforce_data = []
    for path in [
        "loyalty_program/loyalty-salesforce.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            salesforce_data.append(file.read())
    return salesforce_data


@pytest.mark.asyncio
async def test_load_salesforce_no_user_id(
    loyalty_program_salesforce: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_salesforce_test(
        loyalty_program_salesforce, myskoda, responses, mock_user_response_func=mock_user_response
    )


@pytest.mark.asyncio
async def test_load_salesforce_with_user_id(
    loyalty_program_salesforce: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_salesforce_test(
        loyalty_program_salesforce, myskoda, responses, mock_user_response_func=None
    )


@pytest.mark.asyncio
async def test_load_salesforce_with_user_id_anonymize(
    loyalty_program_salesforce: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_salesforce_test(
        loyalty_program_salesforce,
        myskoda,
        responses,
        anonymized=True,
        mock_user_response_func=None,
    )


async def load_loyalty_program_salesforce_test(
    salesforce_data: list[str],
    myskoda: MySkoda,
    responses: aioresponses,
    anonymized: bool = False,
    mock_user_response_func: Callable[[str, aioresponses], str] | None = None,
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    for salesforce_input in salesforce_data:
        salesforce_json = json.loads(salesforce_input)

        user_id = await prepare_user_response_mock(
            responses, DEFAULT_USER_ID, mock_user_response_func
        )
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/loyalty-program/salesforce-contacts/{DEFAULT_USER_ID}",
            body=salesforce_input,
        )
        get_salesforce_result = await myskoda.get_loyalty_program_salesforce_contacts(
            user_id=user_id, anonymize=anonymized
        )
        # Add assertions for vehicle renders result

        assert get_salesforce_result is not None
        if anonymized:
            assert (
                get_salesforce_result.contact_id
                == sha256(salesforce_json["contactId"].encode()).hexdigest()
            )
        else:
            assert get_salesforce_result.contact_id == salesforce_json["contactId"]


@pytest.fixture(name="loyalty_program_transactions")
def load_loyalty_program_transactions() -> list[str]:
    """Load loyalty program transactions fixture."""
    transactions_data = []
    for path in [
        "loyalty_program/loyalty-transactions.json",
    ]:
        with FIXTURES_DIR.joinpath(path).open() as file:
            transactions_data.append(file.read())
    return transactions_data


@pytest.mark.asyncio
async def test_load_transactions_no_user_id(
    loyalty_program_transactions: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_transactions_test(
        loyalty_program_transactions, myskoda, responses, mock_user_response_func=mock_user_response
    )


@pytest.mark.asyncio
async def test_load_transactions_with_user_id(
    loyalty_program_transactions: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_transactions_test(
        loyalty_program_transactions, myskoda, responses, mock_user_response_func=None
    )


@pytest.mark.asyncio
async def test_load_transactions_with_user_id_anonymize(
    loyalty_program_transactions: list[str], myskoda: MySkoda, responses: aioresponses
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    await load_loyalty_program_transactions_test(
        loyalty_program_transactions,
        myskoda,
        responses,
        anonymized=True,
        mock_user_response_func=None,
    )


async def load_loyalty_program_transactions_test(
    transactions_data: list[str],
    myskoda: MySkoda,
    responses: aioresponses,
    anonymized: bool = False,
    mock_user_response_func: Callable[[str, aioresponses], str] | None = None,
) -> None:
    """Example unit test for RestAPI.get_loyalty_program_badge()."""
    for transactions_input in transactions_data:
        transactions_json = json.loads(transactions_input)

        user_id = await prepare_user_response_mock(
            responses, DEFAULT_USER_ID, mock_user_response_func
        )
        responses.get(
            url=f"https://mysmob.api.connect.skoda-auto.cz/api/v2/loyalty-program/members/{DEFAULT_USER_ID}/transactions",
            body=transactions_input,
        )
        get_transactions_result = await myskoda.get_loyalty_program_transactions(
            user_id=user_id, anonymize=anonymized
        )
        # Add assertions for vehicle renders result

        assert get_transactions_result is not None
        assert get_transactions_result.transactions is not None
        transactions_list = get_transactions_result.transactions
        transactions_list_json = transactions_json["transactions"]
        assert len(transactions_list) == len(transactions_list_json)
        for i in range(len(transactions_list)):
            transaction = transactions_list[i]
            transaction_json = transactions_list_json[i]
            if anonymized:
                assert transaction.id == sha256(transaction_json["id"].encode()).hexdigest()
            else:
                assert transaction.id == transaction_json["id"]
            assert transaction.type == transaction_json["type"]
            assert transaction.name == transaction_json["name"]
            assert transaction.points_amount == transaction_json["pointsAmount"]
            assert transaction.timestamp == datetime.fromisoformat(transaction_json["timestamp"])
