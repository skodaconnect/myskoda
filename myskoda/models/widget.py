"""Models for responses of /v2/widgets/vehicle-status/{vin} endpoint."""

from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .position import ParkingCoordinates

from .common import BaseResponse


@dataclass
class WidgetVehicle(DataClassORJSONMixin):
    name: str
    license_plate: str = field(metadata=field_options(alias="licensePlate"))
    render_url: str = field(metadata=field_options(alias="renderUrl"))


@dataclass
class WidgetVehicleStatus(DataClassORJSONMixin):
    doors_locked: str = field(metadata=field_options(alias="doorsLocked"))
    driving_range_in_km: int = field(metadata=field_options(alias="drivingRangeInKm"))


@dataclass
class ParkingMaps(DataClassORJSONMixin):
    light_map_url: str = field(metadata=field_options(alias="lightMapUrl"))


@dataclass
class WidgetParkingPosition(ParkingCoordinates):
    state: str
    maps: ParkingMaps


@dataclass
class WidgetResponse(BaseResponse):
    vehicle: WidgetVehicle
    vehicle_status: WidgetVehicleStatus = field(metadata=field_options(alias="vehicleStatus"))
    parking_position: WidgetParkingPosition = field(metadata=field_options(alias="parkingPosition"))
