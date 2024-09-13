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


class OpenState(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNSUPPORTED = "UNSUPPORTED"


class DoorLockedState(str, Enum):
    LOCKED = "YES"
    UNLOCKED = "NO"


class ChargerLockedState(str, Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"


class ConnectionState(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


class Side(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
