"""Models for responses of /api/v2/widgets/vehicle-status/{vin} endpoint."""

from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import BaseResponse
from .position import ParkingCoordinates


@dataclass
class ChargingStatus(DataClassORJSONMixin):
    state_of_charge_in_percent: int = field(metadata=field_options(alias="stateOfChargeInPercent"))
    remaining_time_to_fully_charged_in_minutes: int = field(
        metadata=field_options(alias="remainingTimeToFullyChargedInMinutes")
    )


@dataclass
class Vehicle(DataClassORJSONMixin):
    name: str
    license_plate: str = field(metadata=field_options(alias="licensePlate"))
    render_url: str = field(metadata=field_options(alias="renderUrl"))


@dataclass
class VehicleStatus(DataClassORJSONMixin):
    doors_locked: str = field(metadata=field_options(alias="doorsLocked"))
    driving_range_in_km: int = field(metadata=field_options(alias="drivingRangeInKm"))


@dataclass
class Maps(DataClassORJSONMixin):
    light_map_url: str = field(metadata=field_options(alias="lightMapUrl"))


@dataclass
class ParkingPosition(ParkingCoordinates):
    state: str
    maps: Maps


@dataclass
class WidgetResponse(BaseResponse):
    vehicle: Vehicle
    vehicle_status: VehicleStatus = field(metadata=field_options(alias="vehicleStatus"))
    parking_position: ParkingPosition = field(metadata=field_options(alias="parkingPosition"))
    charging_status: ChargingStatus | None = field(
        default=None, metadata=field_options(alias="chargingStatus")
    )
