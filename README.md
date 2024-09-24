![Version](https://img.shields.io/github/v/release/skodaconnect/myskoda?include_prereleases)
![PyPi](https://img.shields.io/pypi/v/myskoda?label=latest%20pypi)
![Downloads PyPi](https://img.shields.io/pypi/dm/myskoda)

# MySkoda

This Python library can be used to work with the MySkoda API.

<!-- TOC -->

- [MySkoda](#myskoda)
    - [Getting Started](#getting-started)
    - [Primer](#primer)
        - [Performing Operations](#performing-operations)
        - [Subscribing to Events](#subscribing-to-events)
    - [As Library](#as-library)
        - [Basic example](#basic-example)
    - [As CLI](#as-cli)
    - [Usage](#usage)
        - [Subscribing to Events](#subscribing-to-events)
        - [Fetching data](#fetching-data)
            - [Info](#info)
            - [Charging](#charging)
            - [Status](#status)

<!-- /TOC -->

## Getting Started

The MySkoda package is published to Pypi and can be found [here](https://pypi.org/project/myskoda/).

It can be installed the usual way:

```sh
pip install myskoda
```

## Primer

MySkoda relies on two ways to connect to the Skoda servers:

* **MQTT** (For realtime information and for checking whether operations were performed by the car.)
* **HTTP Api** (For retrieving detailed information and initiating operations.)

### Performing Operations

Every operation is executed the following way:

1. An HTTP request to the MySkoda servers is executed, initiating the desired operation (e.g. starting window heating)
2. The HTTP request will immediately return status 200, no matter whether it is successful or not.
3. An MQTT message with an `OperationRequest` is is published. It will be status `IN_PROGRESS`.
4. At some point, the vehicle will pick up the operation and perform it.
5. An MQTT message with an `OperationRequest` and status `COMPLETED_SUCCESS` will be published.
6. The operation is completed.

### Subscribing to Events

The vehicle will proactively send `ServiceEvent` messages to the MQTT broker. These events are very generic and most of them contain no meaningful data or information about what exactly happened.

When a message with `ServiceEvent` is received, detailed information can be gathered from the Rest API.

## As Library

MySkoda relies on [aiohttp](https://pypi.org/project/aiohttp/) which must be installed.
A `ClientSession` must be opened and passed to `MySkoda` upon initialization.

After connecting, operations can be performed, events can be subscribed to and data can be loaded from the API.

Don't forget to close the session and disconnect MySkoda after you're done.

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

## Usage

### Subscribing to Events

After initializing ([see basic example](#basic-example)), it is possible to subscribe to events for a specific vehicle.

Internally, MySkoda will always connect to all MQTT topics that it can subscribe to, after loading a list of all vehicle identification numbers.

```python
from myskoda.event import Event

def on_event(event: Event):
    pass

myskoda.subscribe(on_event)
```

The suggested approach is to check the event's `type` field to see what it contains. If you're using mypy or pyright, this will also narrow down the event's type and allow you to access specific fields:

```python
from myskoda.event import Event, EventType, ServiceEventTopic

def on_event(event: Event):
    if event.type == EventType.SERVICE_EVENT:
        print("Received service event.")
        if event.topic == ServiceEventTopic.CHARGING:
            print(f"Battery is {event.event.data.soc}% charged.")
```

There is three types of events:

* `EventType.SERVICE_EVENT`: Sent proactively by the vehicle, when something changed.
* `EventType.OPERATION`: Sent by Skoda's server as response to an operation executed on the vehicle. It will track the operation's status.
* `EventType.ACCOUNT_EVENT`

### Fetching data

After initializing ([see basic example](#basic-example)), it is possible to fetch data directly from the `MySkoda` object.
Simply call and await the getter for whatever data is needed.

#### Info

This endpoint contains static information about the vehicle, such as the engine type, the model and model year, settings and other things that seldomly change.

```python
from myskoda.models.info import Info

vin = "TMBJB9NY6RF999999" # See `MySkoda.list_vehicle_vins()`.
info = await myskoda.get_info(vin)
print(f"Vehicle is a {info.get_model_name()}.")
```

#### Charging

Charging related information such as current battery soc and so on. 

```python
from myskoda.models.charging import Charging

vin = "TMBJB9NY6RF999999" # See `MySkoda.list_vehicle_vins()`.
charging: Charging = await myskoda.get_charging(vin)
soc = charging.status.battery.state_of_charge_in_percent
print(f"Vehicle is {soc}% charged.")
```

#### Status

All temporary status information for a vehicle, such whether it is locked or opened, the lights are on and therelike.

```python
from myskoda.models.status import Status
from myskoda.models.common import DoorLockedState

vin = "TMBJB9NY6RF999999" # See `MySkoda.list_vehicle_vins()`.
status: Status = await myskoda.get_status(vin)
if status.overall.doors_locked == DoorLockedState.UNLOCKED:
    print("Vehicle is not locked.")
```