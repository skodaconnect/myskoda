"""Represents a whole vehicle."""

from .models.air_conditioning import AirConditioning
from .models.auxiliary_heating import AuxiliaryHeating
from .models.charging import Charging
from .models.driving_range import DrivingRange
from .models.health import Health
from .models.info import CapabilityId, Info
from .models.maintenance import Maintenance
from .models.position import Positions
from .models.status import Status
from .models.trip_statistics import TripStatistics


class Vehicle:
    """Main model for a Vehicle. Holds all Vehicle information."""

    info: Info
    charging: Charging | None = None
    status: Status | None = None
    air_conditioning: AirConditioning | None = None
    auxiliary_heating: AuxiliaryHeating | None = None
    positions: Positions | None = None
    driving_range: DrivingRange | None = None
    trip_statistics: TripStatistics | None = None
    maintenance: Maintenance
    health: Health | None = None

    def __init__(self, info: Info, maintenance: Maintenance) -> None:  # noqa: D107
        self.info = info
        self.maintenance = maintenance

    def has_capability(self, cap: CapabilityId) -> bool:
        """Check for a capability.

        Checks whether a vehicle generally has a capability.
        Does not check whether it's actually available.
        """
        return self.info.has_capability(cap)

    def is_capability_available(self, cap: CapabilityId) -> bool:
        """Check for capability availability.

        Checks whether the vehicle has the capability and whether it is currently
        available. A capability can be unavailable for example if it's deactivated
        by the currently active user.
        """
        return self.info.is_capability_available(cap)
