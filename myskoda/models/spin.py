"""Models for responses of api/v2/garage/vehicles/{vin}."""

import logging
from dataclasses import dataclass, field
from enum import StrEnum

from mashumaro.mixins.orjson import DataClassORJSONMixin

_LOGGER = logging.getLogger(__name__)

class VerificationStatus(StrEnum):
    """List of known statuses for SPIN."""
    CORRECT_SPIN = "CORRECT_SPIN"
    INCORRECT_SPIN = "INCORRECT_SPIN"

@dataclass
class SpinStatus(DataClassORJSONMixin):
    state: str
    remainingTries: int
    lockedWaitingTimeInSeconds: int

@dataclass
class Spin(DataClassORJSONMixin):
    verificationStatus: VerificationStatus
    spinStatus: SpinStatus | None = field(default=None)
