"""Command for sending raw requests to the MySkoda API."""

import json
import sys
from typing import TYPE_CHECKING

import asyncclick as click
from aiohttp.client_exceptions import ClientResponseError
from asyncclick.core import Context

if TYPE_CHECKING:
    from myskoda import MySkoda


@click.command()
@click.argument("path")
@click.option("vin", "--vin", help="VIN to substitute into {vin} placeholders in the path.")
@click.option(
    "method",
    "--method",
    "-X",
    help="HTTP method. Defaults to GET, or POST when data is provided on stdin.",
    type=click.Choice(["GET", "POST", "PUT", "DELETE", "PATCH"], case_sensitive=False),
    default=None,
)
@click.pass_context
async def raw_request(ctx: Context, path: str, vin: str | None, method: str | None) -> None:
    """Send a raw authenticated request to the MySkoda API.

    PATH is the API path, e.g. /v2/garage or /v1/charging/{vin}/set-charging-current.
    The base URL (https://mysmob.api.connect.skoda-auto.cz/api) is prepended automatically.

    JSON data can be piped via stdin; when data is present the method defaults to POST.

    Examples:

    \b
        myskoda [...] raw-request /v2/garage
        echo '{"chargingCurrent": 20}' | myskoda [...] raw-request --vin TMBJB9NY \\
            '/v1/charging/{vin}/set-charging-current'
    """
    myskoda: MySkoda = ctx.obj["myskoda"]

    if vin:
        path = path.replace("{vin}", vin)

    body: dict | None = None
    if not sys.stdin.isatty():
        raw_stdin = sys.stdin.read().strip()
        if raw_stdin:
            try:
                body = json.loads(raw_stdin)
            except json.JSONDecodeError as e:
                msg = f"stdin is not valid JSON: {e}"
                raise click.BadParameter(msg) from e

    method = ("POST" if body is not None else "GET") if method is None else method.upper()

    try:
        text = await myskoda.rest_api.raw_request(url=path, method=method, json=body)
    except ClientResponseError as e:
        ctx.obj["print"]({"error": e.status, "message": e.message, "url": str(e.request_info.url)})
        return

    if text:
        try:
            ctx.obj["print"](json.loads(text))
        except json.JSONDecodeError:
            print(text)
    else:
        ctx.obj["print"]({"status": "ok"})
