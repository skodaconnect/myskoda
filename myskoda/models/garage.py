"""Models for responses of api/v2/garage/vehicles/{vin}."""

import logging
from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from myskoda.models.info import CompositeRender, Error, Render, VehicleState

_LOGGER = logging.getLogger(__name__)


@dataclass
class GarageEntry(DataClassORJSONMixin):
    """One vehicle in the list of vehicles."""

    vin: str
    name: str
    state: VehicleState
    title: str
    priority: int
    device_platform: str = field(metadata=field_options(alias="devicePlatform"))
    system_model_id: str = field(metadata=field_options(alias="systemModelId"))
    renders: list[Render]
    composite_renders: list[CompositeRender] = field(
        metadata=field_options(alias="compositeRenders")
    )


@dataclass
class Garage(DataClassORJSONMixin):
    """Contents of the users Garage."""

    vehicles: list[GarageEntry] | None = field(default=None)
    errors: list[Error] | None = field(default=None)
