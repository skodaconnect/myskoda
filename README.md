[![Version](https://img.shields.io/github/v/release/skodaconnect/myskoda?include_prereleases)](https://github.com/skodaconnect/myskoda/releases)
[![PyPi](https://img.shields.io/pypi/v/myskoda?label=latest%20pypi)](https://pypi.org/project/myskoda/)
[![Downloads PyPi](https://img.shields.io/pypi/dm/myskoda)](https://pypi.org/project/myskoda/)
[![Docs](https://readthedocs.org/projects/myskoda/badge/?version=latest)](https://myskoda.readthedocs.io/en/latest/)
[![Discord](https://img.shields.io/discord/877164727636230184)](https://discord.gg/t7az2hSJXq)

# MySkoda

This Python library can be used to work with the MySkoda API.
<!-- TOC -->

- [MySkoda](#myskoda)
    - [Get In Touch](#get-in-touch)
    - [Quick Start](#quick-start)
        - [Basic example](#basic-example)
    - [Documentation](#documentation)
    - [As Library](#as-library)
    - [As CLI](#as-cli)

<!-- /TOC -->

## Get In Touch

We have an active community in our discord. [Feel free to join](https://discord.gg/t7az2hSJXq).

If you have any issues, please report them in our issue tracker.

## Quick Start

The MySkoda package is published to Pypi and can be found [here](https://pypi.org/project/myskoda/).

It can be installed the usual way:

```sh
pip install myskoda
```

### Basic example

```python
from aiohttp import ClientSession
from myskoda import MySkoda

session = ClientSession()
myskoda = MySkoda(session)
await myskoda.connect(email, password)

for vin in await myskoda.list_vehicle_vins():
    print(vin)

myskoda.disconnect()
await session.close()
```

## Documentation

Detailed documentation [is available at read the docs](https://myskoda.readthedocs.io/en/latest/):
* [Fetching Data](https://myskoda.readthedocs.io/en/latest/fetching-data/)
* [Subscribing to Events](https://myskoda.readthedocs.io/en/latest/events/)
* [Primer](https://myskoda.readthedocs.io/en/latest/primer/)

## As Library

MySkoda relies on [aiohttp](https://pypi.org/project/aiohttp/) which must be installed.
A `ClientSession` must be opened and passed to `MySkoda` upon initialization.

After connecting, operations can be performed, events can be subscribed to and data can be loaded from the API.

Don't forget to close the session and disconnect MySkoda after you're done.

## As CLI

The MySkoda package features a CLI.
You will have to install it with extras `cli`:

```sh
pip install myskoda[cli]
```

Afterwards, the CLI is available in your current environment by invoking `myskoda`.

Username and password must be provided to the CLI for every request as options, before selecting a sub command:

```sh
myskoda --user "user@example.com" --password "super secret" list-vehicles
```

Help can be accessed the usual way:

```sh
myskoda --help
```
