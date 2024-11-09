"""Common constants."""

# Client id extracted from the MySkoda Android app.
CLIENT_ID = "7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com"

BASE_URL_SKODA = "https://mysmob.api.connect.skoda-auto.cz"
BASE_URL_IDENT = "https://identity.vwgroup.io"

MQTT_BROKER_HOST = "mqtt.messagehub.de"
MQTT_BROKER_PORT = 8883


MQTT_OPERATION_TOPICS = [
    "air-conditioning/set-air-conditioning-at-unlock",
    "air-conditioning/set-air-conditioning-seats-heating",
    "air-conditioning/set-air-conditioning-timers",
    "air-conditioning/set-air-conditioning-without-external-power",
    "air-conditioning/set-target-temperature",
    "air-conditioning/start-stop-air-conditioning",
    "auxiliary-heating/start-stop-auxiliary-heating",
    "air-conditioning/start-stop-window-heating",
    "air-conditioning/windows-heating",
    "charging/start-stop-charging",
    "charging/update-battery-support",
    "charging/update-auto-unlock-plug",
    "charging/update-care-mode",
    "charging/update-charge-limit",
    "charging/update-charge-mode",
    "charging/update-charging-profiles",
    "charging/update-charging-current",
    "vehicle-access/honk-and-flash",
    "vehicle-access/lock-vehicle",
    "vehicle-services-backup/apply-backup",
    "vehicle-wakeup/wakeup",
]

MQTT_SERVICE_EVENT_TOPICS = [
    "air-conditioning",
    "charging",
    "departure",
    "vehicle-status/access",
    "vehicle-status/lights",
]

MQTT_ACCOUNT_EVENT_TOPICS = [
    "account-event/privacy",
]
MQTT_KEEPALIVE = 15
MQTT_RECONNECT_DELAY = 5

MAX_RETRIES = 5

REQUEST_TIMEOUT_IN_SECONDS = 300
