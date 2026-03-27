"""MySkoda Vehicle information."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class Gearbox(DataClassORJSONMixin):
    type: str = field(metadata=field_options(alias="type"))


@dataclass
class Engine(DataClassORJSONMixin):
    type: str = field(metadata=field_options(alias="type"))
    power_in_kw: int = field(metadata=field_options(alias="powerInKW"))
    capacity_in_liters: float = field(metadata=field_options(alias="capacityInLiters"))


@dataclass
class VehicleSpecification(DataClassORJSONMixin):
    title: str = field(metadata=field_options(alias="title"))
    manufacturing_date: date = field(metadata=field_options(alias="manufacturingDate"))
    model: str = field(metadata=field_options(alias="model"))
    model_year: str = field(metadata=field_options(alias="modelYear"))
    body: str = field(metadata=field_options(alias="body"))
    trim_level: str = field(metadata=field_options(alias="trimLevel"))
    system_code: str = field(metadata=field_options(alias="systemCode"))
    system_model_id: str = field(metadata=field_options(alias="systemModelId"))
    engine: Engine = field(metadata=field_options(alias="engine"))
    gearbox: Gearbox = field(metadata=field_options(alias="gearbox"))


class ViewPoint(StrEnum):
    EXTERIOR_SIDE = "EXTERIOR_SIDE"
    EXTERIOR_FRONT = "EXTERIOR_FRONT"
    INTERIOR_SIDE = "INTERIOR_SIDE"
    EXTERIOR_REAR = "EXTERIOR_REAR"
    INTERIOR_FRONT = "INTERIOR_FRONT"
    INTERIOR_BOOT = "INTERIOR_BOOT"


class ViewType(StrEnum):
    UNMODIFIED_EXTERIOR_SIDE = "UNMODIFIED_EXTERIOR_SIDE"
    UNMODIFIED_EXTERIOR_FRONT = "UNMODIFIED_EXTERIOR_FRONT"
    UNMODIFIED_INTERIOR_SIDE = "UNMODIFIED_INTERIOR_SIDE"
    UNMODIFIED_EXTERIOR_REAR = "UNMODIFIED_EXTERIOR_REAR"
    UNMODIFIED_INTERIOR_FRONT = "UNMODIFIED_INTERIOR_FRONT"
    UNMODIFIED_INTERIOR_BOOT = "UNMODIFIED_INTERIOR_BOOT"


@dataclass
class CompositeLayer(DataClassORJSONMixin):
    url: str = field(metadata=field_options(alias="url"))
    view_point: ViewPoint = field(metadata=field_options(alias="viewPoint"))
    type: str = field(metadata=field_options(alias="type"))
    order: int = field(metadata=field_options(alias="order"))


@dataclass
class CompositeRenderer(DataClassORJSONMixin):
    view_type: ViewType = field(metadata=field_options(alias="viewType"))
    layers: list[CompositeLayer] = field(metadata=field_options(alias="layers"))


@dataclass
class VehicleInfo(DataClassORJSONMixin):
    device_platform: str = field(metadata=field_options(alias="devicePlatform"))
    renders: list[dict[str, Any]] = field(metadata=field_options(alias="renders"))
    vehicle_specification: VehicleSpecification = field(
        metadata=field_options(alias="vehicleSpecification")
    )
    composite_renderers: list[CompositeRenderer] = field(
        metadata=field_options(alias="compositeRenders")
    )


@dataclass
class VehicleRenders(DataClassORJSONMixin):
    renders: list[dict[str, Any]] = field(metadata=field_options(alias="renders"))
    composite_renderers: list[CompositeRenderer] = field(
        metadata=field_options(alias="compositeRenders")
    )


@dataclass
class Equipment(DataClassORJSONMixin):
    name: str = field(metadata=field_options(alias="name"))
    description: str = field(metadata=field_options(alias="description"))
    video_url: str = field(metadata=field_options(alias="videoUrl"))
    video_thumbnail_url: str = field(metadata=field_options(alias="videoThumbnailUrl"))


@dataclass
class VehicleEquipment(DataClassORJSONMixin):
    equipment: list[Equipment] = field(metadata=field_options(alias="equipment"))


@dataclass
class VehicleFullInfo(DataClassORJSONMixin):
    info: VehicleInfo = field(metadata=field_options(alias="info"))
    equipment: VehicleEquipment = field(metadata=field_options(alias="equipment"))
    renders: VehicleRenders = field(metadata=field_options(alias="renders"))
