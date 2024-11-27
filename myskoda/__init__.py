"""A library for interacting with the MySkoda APIs."""

from .__version__ import __version__
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
from .mqtt import MySkodaMqttClient
from .myskoda import TRACE_CONFIG, MySkoda
from .rest_api import RestApi
from .vehicle import Vehicle

__all__ = [
    "TRACE_CONFIG",
    "Authorization",
    "AuthorizationError",
    "AuthorizationFailedError",
    "IDKAuthorizationCode",
    "IDKSession",
    "MySkoda",
    "MySkodaMqttClient",
    "RestApi",
    "Vehicle",
    "__version__",
    "air_conditioning",
    "charging",
    "common",
    "health",
    "info",
    "operation_request",
    "position",
    "service_event",
    "status",
    "user",
]
