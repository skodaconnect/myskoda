from enum import Enum


class OnOffState(str, Enum):
    ON = "ON"
    OFF = "OFF"


class EnabledState(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class ActiveState(str, Enum):
    ACTIVATED = "ACTIVATED"
    DEACTIVATED = "DEACTIVATED"
