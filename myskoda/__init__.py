"""A library for interacting with the MySkoda APIs."""

from .auth.authorization import (
    Authorization,
    AuthorizationError,
    AuthorizationFailedError,
    IDKAuthorizationCode,
    IDKSession,
)
from .models import (
    air_conditioning,
    charging,
    common,
    health,
    info,
    operation_request,
    position,
    service_event,
    status,
    user,
)
from .mqtt import Mqtt
from .myskoda import TRACE_CONFIG, MySkoda
from .rest_api import RestApi
from .vehicle import Vehicle

__all__ = [
    "Authorization",
    "AuthorizationError",
    "AuthorizationFailedError",
    "IDKAuthorizationCode",
    "IDKSession",
    "air_conditioning",
    "charging",
    "common",
    "health",
    "info",
    "position",
    "status",
    "RestApi",
    "MySkoda",
    "operation_request",
    "service_event",
    "Mqtt",
    "Vehicle",
    "user",
    "TRACE_CONFIG",
]
