"""MySkoda Vehicle information."""

from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from myskoda.models.software_status import SoftwareUpdateStatus

from .common import BaseResponse
from .info import CompositeRender, Info, InfoBase, Render, Specification


@dataclass
class VehicleInfo(InfoBase):
    vehicle_specification: Specification = field(metadata=field_options(alias="vehicleSpecification"))


@dataclass
class VehicleRenders(BaseResponse):
    renders: list[Render]
    composite_renders: list[CompositeRender] = field(
        metadata=field_options(alias="compositeRenders")
    )


@dataclass
class Equipment(DataClassORJSONMixin):
    name: str = field(metadata=field_options(alias="name"))
    description: str = field(metadata=field_options(alias="description"))
    video_url: str = field(metadata=field_options(alias="videoUrl"))
    video_thumbnail_url: str = field(metadata=field_options(alias="videoThumbnailUrl"))


@dataclass
class VehicleEquipment(BaseResponse):
    equipment: list[Equipment] = field(metadata=field_options(alias="equipment"))


@dataclass
class VehicleFullInfo(BaseResponse):
    equipment: VehicleEquipment
    info: VehicleInfo
    renders: VehicleRenders
    software_update_status: SoftwareUpdateStatus
