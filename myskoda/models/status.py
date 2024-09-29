"""Models for responses of api/v2/vehicle-status/{vin}."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum, StrEnum
from urllib.parse import parse_qs, urlparse

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from myskoda.models.common import DoorLockedState, OnOffState, OpenState

_LOGGER = logging.getLogger(__name__)


class CarBodyElements(IntEnum):
    LEFT_FRONT_DOOR = 0
    RIGHT_FRONT_DOOR = 1
    LEFT_BACK_DOOR = 2
    RIGHT_BACK_DOOR = 3
    LEFT_LIGHT = 4
    RIGHT_LIGHT = 5
    TRUNK = 6
    BONNET = 7
    SUNROOF = 8


class CarWindowDoorStates(IntEnum):
    ALL_CLOSED = 1
    WINDOW_OPEN = 2
    DOOR_OPEN = 3


class DoorWindowState(StrEnum):
    CLOSED = "Closed"
    DOOR_OPEN = "Door opened"
    WINDOW_OPEN = "Window opened"


@dataclass
class Detail(DataClassORJSONMixin):
    bonnet: OpenState
    sunroof: OpenState
    trunk: OpenState


@dataclass
class Overall(DataClassORJSONMixin):
    doors: OpenState
    doors_locked: DoorLockedState = field(metadata=field_options(alias="doorsLocked"))
    lights: OnOffState
    locked: DoorLockedState
    windows: OpenState


@dataclass
class RenderMode(DataClassORJSONMixin):
    one_x: str = field(metadata=field_options(alias="oneX"))
    one_and_half_x: str = field(metadata=field_options(alias="oneAndHalfX"))
    two_x: str = field(metadata=field_options(alias="twoX"))
    three_x: str = field(metadata=field_options(alias="threeX"))


@dataclass
class Renders(DataClassORJSONMixin):
    light_mode: RenderMode = field(metadata=field_options(alias="lightMode"))
    dark_mode: RenderMode = field(metadata=field_options(alias="darkMode"))


@dataclass
class Status(DataClassORJSONMixin):
    """Current status information for a vehicle."""

    detail: Detail
    overall: Overall
    renders: Renders
    car_captured_timestamp: datetime | None = field(
        default=None, metadata=field_options(alias="carCapturedTimestamp")
    )

    def _extract_window_door_state_list_from_url(self) -> list[int]:
        """Extract window/door states from renders url.

        Returns:
           States of doors/windows as a list of integers, other elements states are
           ignored since they are available directly in detail or overall fields.

        """
        try:
            parsed_url = urlparse(self.renders.light_mode.one_x)
            parsed_query = parse_qs(parsed_url.query)
            split_values = parsed_query["vehicleState"][0].split("-")
            integer_map = list(map(int, split_values))
        except (IndexError, KeyError, ValueError):
            # Return default if mapping fails
            _LOGGER.exception("Unable to deduct doors/windows state from vehicle status url")
            return [1, 1, 1, 1]
        return integer_map[:4]

    def _get_door_window_state(self, element: CarBodyElements) -> DoorWindowState:
        door_states = self._extract_window_door_state_list_from_url()
        state = door_states[element.value]
        if state == CarWindowDoorStates.ALL_CLOSED.value:
            return DoorWindowState.CLOSED
        if state == CarWindowDoorStates.DOOR_OPEN.value:
            return DoorWindowState.DOOR_OPEN
        if state == CarWindowDoorStates.WINDOW_OPEN.value:
            return DoorWindowState.WINDOW_OPEN
        _LOGGER.debug("Unknown door state: %d", state)
        # Return default as being closed
        return DoorWindowState.CLOSED

    @property
    def left_front_door(self) -> DoorWindowState:
        """State of the left front door."""
        return self._get_door_window_state(CarBodyElements.LEFT_FRONT_DOOR)

    @property
    def right_front_door(self) -> DoorWindowState:
        """State of the right front door."""
        return self._get_door_window_state(CarBodyElements.RIGHT_FRONT_DOOR)

    @property
    def left_back_door(self) -> DoorWindowState:
        """State of the left back door."""
        return self._get_door_window_state(CarBodyElements.LEFT_BACK_DOOR)

    @property
    def right_back_door(self) -> DoorWindowState:
        """State of the right back door."""
        return self._get_door_window_state(CarBodyElements.RIGHT_BACK_DOOR)
