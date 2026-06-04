"""Represents a whole vehicle."""

from datetime import datetime

from .models.air_conditioning import AirConditioning
from .models.auxiliary_heating import AuxiliaryHeating
from .models.charging import Charging
from .models.departure import DepartureInfo
from .models.driving_range import DrivingRange
from .models.health import Health
from .models.info import CapabilityId, Info
from .models.maintenance import Maintenance
from .models.position import ParkingPositionV3, Positions
from .models.software_status import SoftwareUpdateStatus
from .models.status import Status
from .models.trip_statistics import SingleTrips, TripStatistics
from .models.vehicle_connection_status import VehicleConnectionStatus


def _ts_changed(existing_ts: datetime | None, new_ts: datetime | None) -> bool:
    """Return True when the timestamp has changed or was absent."""
    return existing_ts is None or existing_ts != new_ts


class Vehicle:
    """Main model for a Vehicle. Holds all Vehicle information."""

    info: Info
    charging: Charging | None = None
    status: Status | None = None
    air_conditioning: AirConditioning | None = None
    auxiliary_heating: AuxiliaryHeating | None = None
    positions: Positions | None = None
    parking_position: ParkingPositionV3 | None = None
    driving_range: DrivingRange | None = None
    trip_statistics: TripStatistics | None = None
    single_trip_statistics: SingleTrips | None = None
    maintenance: Maintenance
    health: Health | None = None
    departure_info: DepartureInfo | None = None
    connection_status: VehicleConnectionStatus | None = None
    software_update_status: SoftwareUpdateStatus | None = None

    def __init__(self, info: Info, maintenance: Maintenance) -> None:  # pragma: no cover
        self.info = info
        self.maintenance = maintenance

    def update_charging(self, new: Charging) -> bool:
        """Update charging if car_captured_timestamp changed; return True if updated."""
        if not _ts_changed(
            self.charging and self.charging.car_captured_timestamp, new.car_captured_timestamp
        ):
            return False
        self.charging = new
        return True

    def update_status(self, new: Status) -> bool:
        """Update status if car_captured_timestamp changed; return True if updated."""
        if not _ts_changed(
            self.status and self.status.car_captured_timestamp, new.car_captured_timestamp
        ):
            return False
        self.status = new
        return True

    def update_air_conditioning(self, new: AirConditioning) -> bool:
        """Update air_conditioning if car_captured_timestamp changed; return True if updated."""
        if not _ts_changed(
            self.air_conditioning and self.air_conditioning.car_captured_timestamp,
            new.car_captured_timestamp,
        ):
            return False
        self.air_conditioning = new
        return True

    def update_auxiliary_heating(self, new: AuxiliaryHeating) -> bool:
        """Update auxiliary_heating if car_captured_timestamp changed; return True if updated."""
        if not _ts_changed(
            self.auxiliary_heating and self.auxiliary_heating.car_captured_timestamp,
            new.car_captured_timestamp,
        ):
            return False
        self.auxiliary_heating = new
        return True

    def update_driving_range(self, new: DrivingRange) -> bool:
        """Update driving_range if car_captured_timestamp changed; return True if updated."""
        if not _ts_changed(
            self.driving_range and self.driving_range.car_captured_timestamp,
            new.car_captured_timestamp,
        ):
            return False
        self.driving_range = new
        return True

    def update_departure_info(self, new: DepartureInfo) -> bool:
        """Update departure_info if car_captured_timestamp changed; return True if updated."""
        if not _ts_changed(
            self.departure_info and self.departure_info.car_captured_timestamp,
            new.car_captured_timestamp,
        ):
            return False
        self.departure_info = new
        return True

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
