"""MySkoda Vehicle information."""

from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import BaseResponse
from .info import CompositeRender, Render, Specification


@dataclass
class VehicleInfo(DataClassORJSONMixin):
    device_platform: str = field(metadata=field_options(alias="devicePlatform"))
    renders: list[Render] = field(metadata=field_options(alias="renders"))
    vehicle_specification: Specification = field(
        metadata=field_options(alias="vehicleSpecification")
    )
    composite_renderers: list[CompositeRender] = field(
        metadata=field_options(alias="compositeRenders")
    )


@dataclass
class VehicleRenders(BaseResponse):
    renders: list[Render] = field(metadata=field_options(alias="renders"))
    composite_renderers: list[CompositeRender] = field(
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
class VehicleFullInfo(DataClassORJSONMixin):
    info: VehicleInfo = field(metadata=field_options(alias="info"))
    equipment: VehicleEquipment = field(metadata=field_options(alias="equipment"))
    renders: VehicleRenders = field(metadata=field_options(alias="renders"))
