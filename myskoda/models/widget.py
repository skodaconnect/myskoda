"""Models for responses of /api/v2/widgets/vehicle-status/{vin} endpoint."""

from dataclasses import dataclass, field
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import BaseResponse, OpenState
from .position import ParkingCoordinates


@dataclass
class WidgetChargingStatus(DataClassORJSONMixin):
    state_of_charge_in_percent: int = field(metadata=field_options(alias="stateOfChargeInPercent"))
    remaining_time_to_fully_charged_in_minutes: int = field(
        metadata=field_options(alias="remainingTimeToFullyChargedInMinutes")
    )


@dataclass
class WidgetVehicle(DataClassORJSONMixin):
    name: str
    license_plate: str = field(metadata=field_options(alias="licensePlate"))
    render_url: str = field(metadata=field_options(alias="renderUrl"))


@dataclass
class VehicleStatus(DataClassORJSONMixin):
    driving_range_in_km: int = field(metadata=field_options(alias="drivingRangeInKm"))
    doors_locked: OpenState | None = field(
        default=None, metadata=field_options(alias="doorsLocked")
    )


@dataclass
class Maps(DataClassORJSONMixin):
    light_map_url: str = field(metadata=field_options(alias="lightMapUrl"))


class ParkingPositionState(StrEnum):
    PARKED = "PARKED"
    IN_MOTION = "IN_MOTION"


@dataclass
class ParkingPositionInMotion(DataClassORJSONMixin):
    state: ParkingPositionState


@dataclass
class ParkingPositionParked(ParkingCoordinates, ParkingPositionInMotion):
    maps: Maps


@dataclass
class WidgetResponse(BaseResponse):
    vehicle: WidgetVehicle
    vehicle_status: VehicleStatus = field(metadata=field_options(alias="vehicleStatus"))
    parking_position: ParkingPositionParked | ParkingPositionInMotion = field(
        metadata=field_options(alias="parkingPosition")
    )
    charging_status: WidgetChargingStatus | None = field(
        default=None, metadata=field_options(alias="chargingStatus")
    )
