"""Common constants."""

# Client id extracted from the MySkoda Android app.
CLIENT_ID = "7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com"
REDIRECT_URI = "myskoda://redirect/login/"

BASE_URL_SKODA = "https://mysmob.api.connect.skoda-auto.cz"
BASE_URL_IDENT = "https://identity.vwgroup.io"
BASE_URL_CHARGING = "https://prod.emea.mobile.charging.cariad.digital"

MQTT_BROKER_HOST = "mqtt.messagehub.de"
MQTT_BROKER_PORT = 8883

FIREBASE_ANDROID_CERT = "E567A2E2E6C5E889CDB37EF07EBEC1576C196325"
FIREBASE_ANDROID_FCM_CLIENT_VERSION = "fcm-25.0.1"
FIREBASE_ANDROID_FIS_SDK_VERSION = "a:19.0.1"
FIREBASE_ANDROID_OS_VERSION = "35"
FIREBASE_ANDROID_PACKAGE = "cz.skodaauto.myskoda"
FIREBASE_API_KEY = "AIzaSyBlJdDfVR6ltRhKpA87F3SmCe2hHqhyEd8"
FIREBASE_APP_ID = "1:678067506455:android:4afca86c91d6d4c235bb52"
FIREBASE_GMS_VERSION = "260000000"
FIREBASE_PROJECT_ID = "678067506455"
FIREBASE_REGISTER_DEFAULT_RETRIES = 3
FIREBASE_SENDER_ID = "678067506455"
MYSKODA_APP_VERSION = "8.12.0"
MYSKODA_APP_VERSION_CODE = "260430001"

MQTT_OPERATION_TIMEOUT = 10 * 60  #  10 minutes
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
    "departure/update-departure-timers",
    "departure/update-minimal-soc",
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
    "vehicle-status/odometer",
]

MQTT_VEHICLE_EVENT_TOPICS = [
    "vehicle-connection-status-update",
    "vehicle-ignition-status",
]

MQTT_ACCOUNT_EVENT_TOPICS = [
    "account-event/privacy",
]
MQTT_KEEPALIVE = 60
MQTT_RECONNECT_DELAY = 5
MQTT_MAX_RECONNECT_DELAY = 120
MQTT_FAST_RETRY = 10
# Maximum time (seconds) MySkodaMqttClient.connect() will block waiting for the
# initial subscription before raising.
MQTT_CONNECT_TIMEOUT = 600
# Minimum time (seconds) that must elapse between two FCM token refreshes
# triggered by MQTT auth failures. The MySkoda broker can take a while to start
# accepting a newly registered token, so we throttle to avoid spamming new
# registrations during that window.
MQTT_MIN_FCM_REFRESH_INTERVAL = 120

MAX_RETRIES = 5

CACHE_USER_ENDPOINT_IN_HOURS = 6
CACHE_VEHICLE_HEALTH_IN_HOURS = 6
CACHE_CLOCK_SKEW_TOLERANCE_IN_HOURS = 4

REQUEST_TIMEOUT_IN_SECONDS = 300
DEFAULT_DEBOUNCE_WAIT_SECONDS = 10.0
OPERATION_REFRESH_DELAY_SECONDS = 5.0
