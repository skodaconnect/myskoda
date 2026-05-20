"""Utilities for the command line interface."""

import json
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from functools import update_wrapper
from typing import TYPE_CHECKING, Any

import aiofiles
import asyncclick as click
import yaml
from aiohttp.client_exceptions import ClientResponseError
from asyncclick.core import Context
from dateutil.parser import isoparse
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexer import Lexer
from pygments.lexers import JsonLexer, YamlLexer

if TYPE_CHECKING:
    from myskoda import MySkoda

# TODO(@dvx76): put in ~/.config/myskoda or Windows equivalent. Respect $XDG_CONFIG
TOKENS_FILE = ".tokens.json"


async def handle_request(
    ctx: Context,
    func: Callable[..., Awaitable],
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> None:
    """Handle API requests and perform error handling."""
    try:
        result = await func(*args, **kwargs)
        if hasattr(result, "to_dict"):
            ctx.obj["print"](result.to_dict())
        else:
            ctx.obj["print"](result)
    except ClientResponseError as e:
        ctx.obj["print"]({"error": e.status, "message": e.message, "url": str(e.request_info.url)})


def mqtt_required[R](func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[Awaitable[R]]]:
    """Enable MQTT before connecting to MySkoda."""

    @click.pass_context
    async def new_func(ctx: Context, *args, **kwargs) -> Awaitable[R]:  # noqa: ANN002, ANN003
        if ctx.obj["mqtt_disabled"]:
            return await ctx.invoke(func, *args, **kwargs)
        myskoda: MySkoda = ctx.obj["myskoda"]
        await myskoda.enable_mqtt()
        return await ctx.invoke(func, *args, **kwargs)

    return update_wrapper(new_func, func)


class Format(StrEnum):
    JSON = "json"
    YAML = "yaml"


def highlight_for_console(text: str, lexer: Lexer) -> str:
    if sys.stdout.isatty():
        return highlight(text, lexer, TerminalFormatter())
    return text


def print_json(data: dict) -> None:
    print(highlight_for_console(json.dumps(data, indent=4, ensure_ascii=False), JsonLexer()))


def print_yaml(data: dict) -> None:
    print(highlight_for_console(yaml.dump(data, allow_unicode=True), YamlLexer()))


def iso8601_datetime(
    _: click.Context,
    param: click.Parameter,
    value: str | None,
) -> datetime | None:
    if value is None:
        return None
    try:
        return isoparse(value)
    except (ValueError, TypeError) as e:
        err_str = f"{param.name} must be a valid ISO8601 datetime"
        raise click.BadParameter(err_str) from e


def simple_date(
    _: click.Context,
    param: click.Parameter,
    value: str | None,
) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
    except (ValueError, TypeError) as e:
        err_str = f"{param.name} must be a valid YYYY-MM-DD date"
        raise click.BadParameter(err_str) from e


async def load_tokens() -> dict[str, str]:
    try:
        async with aiofiles.open(TOKENS_FILE, encoding="utf-8") as file_handle:
            contents = await file_handle.read()
    except FileNotFoundError:
        return {}
    return json.loads(contents)


async def save_tokens(tokens: dict[str, str]) -> None:
    async with aiofiles.open(TOKENS_FILE, "w", encoding="utf-8") as file_handle:
        await file_handle.write(json.dumps(tokens))


@dataclass
class MethodArgument:
    timestamp: datetime | None = None
    flag: bool | None = None
    text: str | None = None
