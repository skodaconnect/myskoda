"""Skoda Connect API - Extrahierte API-Aufrufe.

Alle HTTP-Aufrufe aus dem MySkoda-Projekt extrahiert,
sodass sie eigenständig wiederverwendet werden können.

Base URLs:
  - API:  https://mysmob.api.connect.skoda-auto.cz
  - Auth: https://identity.vwgroup.io

Auth: OAuth2 PKCE + OpenID Connect
  - Client ID: 7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com
  - Redirect URI: myskoda://redirect/login/

Alle API-Aufrufe verwenden Bearer Token im Header:
  Authorization: Bearer <access_token>
"""

# ==============================================================================
# KONSTANTEN
# ==============================================================================

BASE_URL_SKODA = "https://mysmob.api.connect.skoda-auto.cz"
BASE_URL_IDENT = "https://identity.vwgroup.io"
CLIENT_ID = "7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com"
REDIRECT_URI = "myskoda://redirect/login/"

MQTT_BROKER_HOST = "mqtt.messagehub.de"
MQTT_BROKER_PORT = 8883

# Scopes für OpenID Connect
OIDC_SCOPES = (
    "address badge birthdate cars driversLicense dealers email mileage mbb "
    "nationalIdentifier openid phone profession profile vin"
)

# ==============================================================================
# AUTHENTIFIZIERUNG (4 Schritte)
# ==============================================================================

AUTH_CALLS = {
    # --- Schritt 1: OIDC Authorize ---
    "oidc_authorize": {
        "method": "GET",
        "url": f"{BASE_URL_IDENT}/oidc/v1/authorize",
        "params": {
            "client_id": CLIENT_ID,
            "nonce": "<random_16_char_alphanumeric>",
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": OIDC_SCOPES,
            "code_challenge": "<sha256_base64url(verifier)>",
            "code_challenge_method": "s256",
            "prompt": "login",
        },
        "returns": "HTML mit CSRF-Token, relayState, hmac",
    },
    # --- Schritt 2: E-Mail eingeben ---
    "login_identifier": {
        "method": "POST",
        "url": f"{BASE_URL_IDENT}/signin-service/v1/{CLIENT_ID}/login/identifier",
        "content_type": "application/x-www-form-urlencoded",
        "form_data": {
            "relayState": "<from_step_1>",
            "email": "<user_email>",
            "hmac": "<from_step_1>",
            "_csrf": "<from_step_1>",
        },
        "returns": "HTML mit aktualisiertem CSRF-Token",
    },
    # --- Schritt 3: Passwort eingeben ---
    "login_authenticate": {
        "method": "POST",
        "url": f"{BASE_URL_IDENT}/signin-service/v1/{CLIENT_ID}/login/authenticate",
        "content_type": "application/x-www-form-urlencoded",
        "allow_redirects": False,
        "form_data": {
            "relayState": "<from_step_2>",
            "email": "<user_email>",
            "password": "<user_password>",
            "hmac": "<from_step_2>",
            "_csrf": "<from_step_2>",
        },
        "returns": "Redirect-Kette → myskoda://redirect/login/?code=<auth_code>",
        "note": "Alle Redirects folgen bis URL mit 'myskoda://' beginnt. Code aus Query-Param extrahieren.",
    },
    # --- Schritt 4: Auth-Code gegen Tokens tauschen ---
    "exchange_auth_code": {
        "method": "POST",
        "url": f"{BASE_URL_SKODA}/api/v1/authentication/exchange-authorization-code?tokenType=CONNECT",
        "json": {
            "code": "<auth_code_from_step_3>",
            "redirectUri": REDIRECT_URI,
            "verifier": "<pkce_verifier_from_step_1>",
        },
        "returns": {
            "accessToken": "<jwt>",
            "refreshToken": "<jwt>",
            "idToken": "<jwt>",
        },
    },
    # --- Token Refresh ---
    "refresh_token": {
        "method": "POST",
        "url": f"{BASE_URL_SKODA}/api/v1/authentication/refresh-token?tokenType=CONNECT",
        "json": {
            "token": "<refresh_token>",
        },
        "returns": {
            "accessToken": "<jwt>",
            "refreshToken": "<jwt>",
            "idToken": "<jwt>",
        },
        "note": "Access Token wird 10 Min vor Ablauf erneuert. Refresh Token 1 Min vor Ablauf.",
    },
}


# ==============================================================================
# GET ENDPOINTS (Daten lesen)
# ==============================================================================

GET_ENDPOINTS = {
    "get_user": {
        "method": "GET",
        "url": "/api/v1/users",
        "description": "Benutzer-Informationen des eingeloggten Users",
    },
    "get_garage": {
        "method": "GET",
        "url": "/api/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
        "description": "Liste aller Fahrzeuge (Garage)",
    },
    "get_vehicle_info": {
        "method": "GET",
        "url": "/api/v2/garage/vehicles/{vin}?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
        "description": "Detaillierte Fahrzeug-Informationen",
    },
    "get_vehicle_status": {
        "method": "GET",
        "url": "/api/v2/vehicle-status/{vin}",
        "description": "Aktueller Fahrzeugstatus (Türen, Fenster, Lichter)",
    },
    "get_driving_range": {
        "method": "GET",
        "url": "/api/v2/vehicle-status/{vin}/driving-range",
        "description": "Geschätzte Reichweite (Verbrenner/Hybrid/Elektro)",
    },
    "get_charging": {
        "method": "GET",
        "url": "/api/v1/charging/{vin}",
        "description": "Ladestatus",
    },
    "get_charging_profiles": {
        "method": "GET",
        "url": "/api/v1/charging/{vin}/profiles",
        "description": "Ladeprofile",
    },
    "get_charging_history": {
        "method": "GET",
        "url": "/api/v1/charging/{vin}/history?userTimezone=UTC&limit={limit}",
        "description": "Lade-Verlauf (Standard limit=50)",
        "optional_params": {
            "cursor": "<iso8601_datetime>",
            "from": "<iso8601_datetime>",
            "to": "<iso8601_datetime>",
        },
    },
    "get_air_conditioning": {
        "method": "GET",
        "url": "/api/v2/air-conditioning/{vin}",
        "description": "Klimaanlagen-Status",
    },
    "get_auxiliary_heating": {
        "method": "GET",
        "url": "/api/v2/air-conditioning/{vin}/auxiliary-heating",
        "description": "Standheizung-Status",
    },
    "get_positions": {
        "method": "GET",
        "url": "/api/v1/maps/positions?vin={vin}",
        "description": "Aktuelle Fahrzeug-Position",
    },
    "get_parking_position": {
        "method": "GET",
        "url": "/api/v3/maps/positions/vehicles/{vin}/parking",
        "description": "Letzte bekannte Parkposition",
    },
    "get_trip_statistics": {
        "method": "GET",
        "url": "/api/v1/trip-statistics/{vin}?offsetType=week&offset=0&timezone=Europe%2FBerlin",
        "description": "Fahrstatistiken (Wochenübersicht)",
    },
    "get_single_trips": {
        "method": "GET",
        "url": "/api/v1/trip-statistics/{vin}/single-trips?timezone=Europe%2FBerlin",
        "description": "Einzelne Fahrten (detailliert)",
        "optional_params": {
            "from": "<iso8601_datetime>",
            "to": "<iso8601_datetime>",
        },
    },
    "get_maintenance": {
        "method": "GET",
        "url": "/api/v3/vehicle-maintenance/vehicles/{vin}",
        "description": "Wartungsinformationen, Einstellungen und Historie",
    },
    "get_maintenance_report": {
        "method": "GET",
        "url": "/api/v3/vehicle-maintenance/vehicles/{vin}/report",
        "description": "Wartungsbericht",
    },
    "get_health": {
        "method": "GET",
        "url": "/api/v1/vehicle-health-report/warning-lights/{vin}",
        "description": "Warnleuchten / Gesundheitsbericht",
    },
    "get_departure_timers": {
        "method": "GET",
        "url": "/api/v1/vehicle-automatization/{vin}/departure/timers?deviceDateTime={url_encoded_datetime}",
        "description": "Abfahrtstimer",
        "note": "deviceDateTime im Format: 2024-01-15T10:30:00.000000+01:00 (URL-encoded)",
    },
    "get_connection_status": {
        "method": "GET",
        "url": "/api/v2/connection-status/{vin}/readiness",
        "description": "Fahrzeug-Verbindungsstatus",
    },
}


# ==============================================================================
# POST ENDPOINTS (Aktionen / Steuerung)
# ==============================================================================

POST_ENDPOINTS = {
    # --- SPIN Verifizierung ---
    "verify_spin": {
        "method": "POST",
        "url": "/api/v1/spin/verify",
        "json": {"currentSpin": "<4-digit-spin>"},
        "description": "S-PIN verifizieren",
    },

    # --- Klimaanlage ---
    "start_air_conditioning": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/start",
        "json": {
            "heaterSource": "ELECTRIC",
            "targetTemperature": {
                "temperatureValue": 21.5,  # in 0.5er Schritten
                "unitInCar": "CELSIUS",
            },
        },
        "description": "Klimaanlage starten",
    },
    "stop_air_conditioning": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/stop",
        "json": None,
        "description": "Klimaanlage stoppen",
    },
    "start_ventilation": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/active-ventilation/start",
        "json": None,
        "description": "Lüftung starten",
    },
    "stop_ventilation": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/active-ventilation/stop",
        "json": None,
        "description": "Lüftung stoppen",
    },
    "start_window_heating": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/start-window-heating",
        "json": None,
        "description": "Scheibenheizung starten",
    },
    "stop_window_heating": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/stop-window-heating",
        "json": None,
        "description": "Scheibenheizung stoppen",
    },

    # --- Standheizung ---
    "start_auxiliary_heating": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/auxiliary-heating/start",
        "json": {
            "spin": "<4-digit-spin>",
            # Optional weitere Config-Felder (z.B. Dauer, Temperatur)
        },
        "description": "Standheizung starten (benötigt SPIN)",
    },
    "stop_auxiliary_heating": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/auxiliary-heating/stop",
        "json": None,
        "description": "Standheizung stoppen",
    },

    # --- Klimaanlage Einstellungen ---
    "set_ac_without_external_power": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/settings/ac-without-external-power",
        "json": {"airConditioningWithoutExternalPowerEnabled": True},
        "description": "Klimaanlage ohne externe Stromversorgung ein/ausschalten",
    },
    "set_ac_at_unlock": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/settings/ac-at-unlock",
        "json": {"airConditioningAtUnlockEnabled": True},
        "description": "Klimaanlage beim Entriegeln ein/ausschalten",
    },
    "set_windows_heating": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/settings/windows-heating",
        "json": {"windowHeatingEnabled": True},
        "description": "Scheibenheizung mit Klimaanlage ein/ausschalten",
    },
    "set_seats_heating": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/settings/seats-heating",
        "json": {
            # Felder variieren je nach Fahrzeug
            "frontLeft": True,
            "frontRight": True,
        },
        "description": "Sitzheizung mit Klimaanlage ein/ausschalten",
    },
    "set_target_temperature": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/settings/target-temperature",
        "json": {
            "temperatureValue": 21.5,  # in 0.5er Schritten
            "unitInCar": "CELSIUS",
        },
        "description": "Zieltemperatur der Klimaanlage setzen",
    },

    # --- Timer ---
    "set_ac_timer": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/timers",
        "json": {
            "timers": [
                {
                    "id": 1,
                    "enabled": True,
                    "time": "07:30",
                    "recurringOn": {"monday": True, "tuesday": False, "...": "..."},
                    # Weitere Felder je nach Timer-Typ
                }
            ]
        },
        "description": "Klimaanlagen-Timer setzen",
    },
    "set_auxiliary_heating_timer": {
        "method": "POST",
        "url": "/api/v2/air-conditioning/{vin}/auxiliary-heating/timers",
        "json": {
            "spin": "<4-digit-spin>",
            "timers": [
                {
                    "id": 1,
                    "enabled": True,
                    "time": "07:30",
                    "recurringOn": {"monday": True, "...": "..."},
                }
            ],
        },
        "description": "Standheizungs-Timer setzen (benötigt SPIN)",
    },
    "set_departure_timer": {
        "method": "POST",
        "url": "/api/v1/vehicle-automatization/{vin}/departure/timers",
        "json": {
            "deviceDateTime": "<iso8601_datetime>",
            "timers": [
                {
                    "id": 1,
                    "enabled": True,
                    # Timer-Konfiguration
                }
            ],
        },
        "description": "Abfahrtstimer setzen",
    },
    "set_departure_timer_settings": {
        "method": "POST",
        "url": "/api/v1/vehicle-automatization/{vin}/departure/timers/settings",
        "json": {"minimumBatteryStateOfChargeInPercent": 40},
        "description": "Mindest-Batteriestand für Abfahrtstimer setzen",
    },

    # --- Laden ---
    "start_charging": {
        "method": "POST",
        "url": "/api/v1/charging/{vin}/start",
        "json": None,
        "description": "Laden starten",
    },
    "stop_charging": {
        "method": "POST",
        "url": "/api/v1/charging/{vin}/stop",
        "json": None,
        "description": "Laden stoppen",
    },
    "set_charge_mode": {
        "method": "POST",
        "url": "/api/v1/charging/{vin}/set-charge-mode",
        "json": {"chargeMode": "MANUAL"},  # oder andere Modi
        "description": "Lademodus setzen",
    },

    # --- Fahrzeugzugriff ---
    "lock_vehicle": {
        "method": "POST",
        "url": "/api/v1/vehicle-access/{vin}/lock",
        "json": {"currentSpin": "<4-digit-spin>"},
        "description": "Fahrzeug verriegeln (benötigt SPIN)",
    },
    "unlock_vehicle": {
        "method": "POST",
        "url": "/api/v1/vehicle-access/{vin}/unlock",
        "json": {"currentSpin": "<4-digit-spin>"},
        "description": "Fahrzeug entriegeln (benötigt SPIN)",
    },
    "honk_and_flash": {
        "method": "POST",
        "url": "/api/v1/vehicle-access/{vin}/honk-and-flash",
        "json": {
            "mode": "HONK_AND_FLASH",  # oder "FLASH" (nur Blinken)
            "vehiclePosition": {
                "latitude": 48.1234,
                "longitude": 11.5678,
            },
        },
        "description": "Hupen und Blinken (oder nur Blinken mit mode=FLASH)",
    },

    # --- Fahrzeug aufwecken ---
    "wakeup": {
        "method": "POST",
        "url": "/api/v1/vehicle-wakeup/{vin}?applyRequestLimiter=true",
        "json": None,
        "description": "Fahrzeug aufwecken (max. 3x pro Tag)",
    },
}


# ==============================================================================
# PUT ENDPOINTS (Konfiguration)
# ==============================================================================

PUT_ENDPOINTS = {
    "set_charge_limit": {
        "method": "PUT",
        "url": "/api/v1/charging/{vin}/set-charge-limit",
        "json": {"targetSOCInPercent": 80},
        "description": "Ladelimit in Prozent setzen",
    },
    "set_battery_care_mode": {
        "method": "PUT",
        "url": "/api/v1/charging/{vin}/set-care-mode",
        "json": {"chargingCareMode": "ACTIVATED"},  # oder "DEACTIVATED"
        "description": "Batteriepflege-Modus aktivieren/deaktivieren",
    },
    "set_auto_unlock_plug": {
        "method": "PUT",
        "url": "/api/v1/charging/{vin}/set-auto-unlock-plug",
        "json": {"autoUnlockPlug": "PERMANENT"},  # oder "OFF"
        "description": "Automatisches Entriegeln des Ladesteckers",
    },
    "set_charging_current": {
        "method": "PUT",
        "url": "/api/v1/charging/{vin}/set-charging-current",
        "json": {"chargingCurrent": "MAXIMUM"},  # oder "REDUCED"
        "description": "Ladestrom auf Maximum oder Reduziert setzen",
    },
}


# ==============================================================================
# MQTT TOPICS (Echtzeit-Events)
# ==============================================================================

MQTT_CONFIG = {
    "broker": f"{MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}",
    "protocol": "TLS/SSL (Port 8883)",
    "keepalive": 60,

    "operation_topics": [
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
    ],
    "service_event_topics": [
        "air-conditioning",
        "charging",
        "departure",
        "vehicle-status/access",
        "vehicle-status/lights",
        "vehicle-status/odometer",
    ],
    "vehicle_event_topics": [
        "vehicle-connection-status-update",
        "vehicle-ignition-status",
    ],
    "account_event_topics": [
        "account-event/privacy",
    ],
}


# ==============================================================================
# BEISPIEL: Minimale Nutzung mit aiohttp
# ==============================================================================

EXAMPLE_USAGE = """
import aiohttp
import asyncio

BASE = "https://mysmob.api.connect.skoda-auto.cz"

async def main():
    async with aiohttp.ClientSession() as session:
        # Nach erfolgreicher Auth:
        headers = {"Authorization": f"Bearer {access_token}"}

        # Garage abrufen
        async with session.get(
            f"{BASE}/api/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4",
            headers=headers,
        ) as resp:
            garage = await resp.json()
            print(garage)

        # Fahrzeugstatus
        vin = "TMBJM..."
        async with session.get(
            f"{BASE}/api/v2/vehicle-status/{vin}",
            headers=headers,
        ) as resp:
            status = await resp.json()
            print(status)

        # Klimaanlage starten
        async with session.post(
            f"{BASE}/api/v2/air-conditioning/{vin}/start",
            headers=headers,
            json={
                "heaterSource": "ELECTRIC",
                "targetTemperature": {
                    "temperatureValue": 22.0,
                    "unitInCar": "CELSIUS",
                },
            },
        ) as resp:
            print(resp.status)

asyncio.run(main())
"""

if __name__ == "__main__":
    print("=== Skoda Connect API Reference ===\n")

    print(f"API Base URL:  {BASE_URL_SKODA}")
    print(f"Auth Base URL: {BASE_URL_IDENT}")
    print(f"Client ID:     {CLIENT_ID}")
    print(f"MQTT Broker:   {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")

    print(f"\n--- Auth Calls ({len(AUTH_CALLS)}) ---")
    for name, call in AUTH_CALLS.items():
        print(f"  {call['method']:6s} {name}")

    print(f"\n--- GET Endpoints ({len(GET_ENDPOINTS)}) ---")
    for name, ep in GET_ENDPOINTS.items():
        print(f"  GET    {ep['url']}")
        print(f"         → {ep['description']}")

    print(f"\n--- POST Endpoints ({len(POST_ENDPOINTS)}) ---")
    for name, ep in POST_ENDPOINTS.items():
        print(f"  POST   {ep['url']}")
        print(f"         → {ep['description']}")

    print(f"\n--- PUT Endpoints ({len(PUT_ENDPOINTS)}) ---")
    for name, ep in PUT_ENDPOINTS.items():
        print(f"  PUT    {ep['url']}")
        print(f"         → {ep['description']}")

    total = len(AUTH_CALLS) + len(GET_ENDPOINTS) + len(POST_ENDPOINTS) + len(PUT_ENDPOINTS)
    print(f"\nGesamt: {total} API-Aufrufe")
