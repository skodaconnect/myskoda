# Skoda Connect API Reference

Alle HTTP-Aufrufe aus dem [MySkoda](https://github.com/skodaconnect/myskoda)-Projekt extrahiert und dokumentiert.

## Übersicht

| | |
|---|---|
| **API Base URL** | `https://mysmob.api.connect.skoda-auto.cz` |
| **Auth Base URL** | `https://identity.vwgroup.io` |
| **Client ID** | `7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com` |
| **Redirect URI** | `myskoda://redirect/login/` |
| **MQTT Broker** | `mqtt.messagehub.de:8883` (TLS) |

Alle API-Aufrufe (außer Auth) verwenden den Header:

```
Authorization: Bearer <access_token>
```

---

## Authentifizierung

Die Authentifizierung verwendet **OAuth2 mit PKCE** (Proof Key for Code Exchange) über den VW Identity Server (OpenID Connect). Der Ablauf simuliert den Login-Flow der MySkoda Android-App.

### Vorbereitung

Vor dem Start werden zwei Werte generiert:

1. **Verifier**: Ein zufälliger alphanumerischer String (16 Zeichen) für PKCE
2. **Challenge**: SHA256-Hash des Verifiers, Base64-URL-encoded (ohne Padding)

```python
import hashlib, base64, secrets, string

# Verifier generieren
alphabet = string.ascii_letters + string.digits
verifier = "".join(secrets.choice(alphabet) for _ in range(16))

# Challenge berechnen
verifier_hash = hashlib.sha256(verifier.encode("utf-8")).digest()
challenge = (
    base64.b64encode(verifier_hash)
    .decode("utf-8")
    .replace("+", "-")
    .replace("/", "_")
    .rstrip("=")
)
```

### Schritt 1: OIDC Authorization Request

Initialer Aufruf an den VW Identity Server. Liefert ein HTML-Formular mit CSRF-Token, HMAC und RelayState.

```
GET https://identity.vwgroup.io/oidc/v1/authorize
```

**Query-Parameter:**

| Parameter | Wert |
|---|---|
| `client_id` | `7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com` |
| `nonce` | `<zufälliger 16-Zeichen-String>` |
| `redirect_uri` | `myskoda://redirect/login/` |
| `response_type` | `code` |
| `scope` | `address badge birthdate cars driversLicense dealers email mileage mbb nationalIdentifier openid phone profession profile vin` |
| `code_challenge` | `<sha256_base64url(verifier)>` |
| `code_challenge_method` | `s256` |
| `prompt` | `login` |

**Response:** HTML-Seite. Daraus extrahieren:
- `_csrf` — CSRF-Token (aus `<input type="hidden" name="_csrf">`)
- `relayState` — Relay State
- `hmac` — HMAC-Wert

### Schritt 2: E-Mail-Adresse senden

```
POST https://identity.vwgroup.io/signin-service/v1/{client_id}/login/identifier
Content-Type: application/x-www-form-urlencoded
```

**Form-Data:**

| Feld | Wert |
|---|---|
| `relayState` | `<aus Schritt 1>` |
| `email` | `<benutzer@email.de>` |
| `hmac` | `<aus Schritt 1>` |
| `_csrf` | `<aus Schritt 1>` |

**Response:** HTML-Seite mit aktualisiertem CSRF-Token, relayState und hmac für Schritt 3.

### Schritt 3: Passwort senden

```
POST https://identity.vwgroup.io/signin-service/v1/{client_id}/login/authenticate
Content-Type: application/x-www-form-urlencoded
```

**Form-Data:**

| Feld | Wert |
|---|---|
| `relayState` | `<aus Schritt 2>` |
| `email` | `<benutzer@email.de>` |
| `password` | `<passwort>` |
| `hmac` | `<aus Schritt 2>` |
| `_csrf` | `<aus Schritt 2>` |

**Wichtig:** `allow_redirects = False` setzen!

**Verhalten:** Der Server antwortet mit einer Redirect-Kette (`Location`-Header). Allen Redirects manuell folgen (jeweils `GET` mit `allow_redirects=False`), bis die URL mit `myskoda://` beginnt.

> Falls ein Redirect `terms-and-conditions` oder `consent/marketing` in der URL enthält, müssen diese zuerst im Browser akzeptiert werden.

**Ergebnis:** Die finale Redirect-URL enthält den Authorization Code:

```
myskoda://redirect/login/?code=<authorization_code>&...
```

### Schritt 4: Authorization Code gegen Tokens tauschen

```
POST https://mysmob.api.connect.skoda-auto.cz/api/v1/authentication/exchange-authorization-code?tokenType=CONNECT
Content-Type: application/json
```

**Request Body:**

```json
{
  "code": "<authorization_code_aus_schritt_3>",
  "redirectUri": "myskoda://redirect/login/",
  "verifier": "<pkce_verifier_aus_schritt_1>"
}
```

**Response:**

```json
{
  "accessToken": "<jwt>",
  "refreshToken": "<jwt>",
  "idToken": "<jwt>"
}
```

### Token Refresh

Der Access Token wird **10 Minuten vor Ablauf** automatisch erneuert. Der Refresh Token wird **1 Minute vor Ablauf** geprüft. Die Ablaufzeit wird aus dem JWT-Payload (`exp`-Feld) gelesen.

```
POST https://mysmob.api.connect.skoda-auto.cz/api/v1/authentication/refresh-token?tokenType=CONNECT
Content-Type: application/json
```

**Request Body:**

```json
{
  "token": "<refresh_token>"
}
```

**Response:**

```json
{
  "accessToken": "<neuer_jwt>",
  "refreshToken": "<neuer_jwt>",
  "idToken": "<neuer_jwt>"
}
```

### Authentifizierung — Sequenzdiagramm

```
Client                          identity.vwgroup.io              mysmob.api.connect.skoda-auto.cz
  │                                      │                                    │
  │──GET /oidc/v1/authorize─────────────>│                                    │
  │<─────HTML (csrf, hmac, relayState)───│                                    │
  │                                      │                                    │
  │──POST /signin-service/.../identifier>│                                    │
  │<─────HTML (csrf, hmac, relayState)───│                                    │
  │                                      │                                    │
  │──POST /signin-service/.../authenticate>                                   │
  │<─────302 Location: ...──────────────>│                                    │
  │──GET Location (follow redirects)────>│                                    │
  │  ... (mehrere 302 Redirects) ...     │                                    │
  │<─────302 myskoda://...?code=XYZ──────│                                    │
  │                                      │                                    │
  │──POST /api/v1/authentication/exchange-authorization-code────────────────->│
  │<─────{ accessToken, refreshToken, idToken }──────────────────────────────│
  │                                      │                                    │
  │  (Alle weiteren API-Calls mit: Authorization: Bearer <accessToken>)       │
```

---

## GET Endpoints — Daten lesen

Alle URLs relativ zu `https://mysmob.api.connect.skoda-auto.cz`.

### Benutzer

#### Benutzer-Informationen

```
GET /api/v1/users
```

Gibt Informationen zum eingeloggten Benutzer zurück.

### Garage / Fahrzeuge

#### Alle Fahrzeuge (Garage)

```
GET /api/v2/garage?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4
```

Liste aller Fahrzeuge des Benutzers.

#### Fahrzeug-Details

```
GET /api/v2/garage/vehicles/{vin}?connectivityGenerations=MOD1&connectivityGenerations=MOD2&connectivityGenerations=MOD3&connectivityGenerations=MOD4
```

Detaillierte Informationen zu einem Fahrzeug.

### Fahrzeugstatus

#### Aktueller Status

```
GET /api/v2/vehicle-status/{vin}
```

Status von Türen, Fenstern, Lichtern etc.

#### Reichweite

```
GET /api/v2/vehicle-status/{vin}/driving-range
```

Geschätzte Reichweite (Verbrenner, Hybrid, Elektro).

#### Verbindungsstatus

```
GET /api/v2/connection-status/{vin}/readiness
```

Online-/Offline-Status des Fahrzeugs.

### Laden

#### Ladestatus

```
GET /api/v1/charging/{vin}
```

Aktueller Ladezustand, Ladeleistung, verbleibende Ladezeit.

#### Ladeprofile

```
GET /api/v1/charging/{vin}/profiles
```

Konfigurierte Ladeprofile.

#### Lade-Verlauf

```
GET /api/v1/charging/{vin}/history?userTimezone=UTC&limit={limit}
```

Standardmäßig `limit=50`. Optionale Filter als Query-Parameter:

| Parameter | Beschreibung |
|---|---|
| `cursor` | ISO 8601 Datetime — Pagination |
| `from` | ISO 8601 Datetime — Start-Datum |
| `to` | ISO 8601 Datetime — End-Datum |

### Klimaanlage / Heizung

#### Klimaanlagen-Status

```
GET /api/v2/air-conditioning/{vin}
```

Aktueller Status der Klimaanlage.

#### Standheizung-Status

```
GET /api/v2/air-conditioning/{vin}/auxiliary-heating
```

Aktueller Status der Standheizung.

### Position

#### Aktuelle Position

```
GET /api/v1/maps/positions?vin={vin}
```

Aktuelle GPS-Position des Fahrzeugs.

#### Parkposition

```
GET /api/v3/maps/positions/vehicles/{vin}/parking
```

Letzte bekannte Parkposition.

### Fahrstatistiken

#### Wochenübersicht

```
GET /api/v1/trip-statistics/{vin}?offsetType=week&offset=0&timezone=Europe%2FBerlin
```

Aggregierte Fahrstatistiken pro Woche.

#### Einzelfahrten

```
GET /api/v1/trip-statistics/{vin}/single-trips?timezone=Europe%2FBerlin
```

Detaillierte Einzelfahrten. Optionale Filter:

| Parameter | Beschreibung |
|---|---|
| `from` | ISO 8601 Datetime — Start-Datum |
| `to` | ISO 8601 Datetime — End-Datum |

### Wartung

#### Wartungsinformationen

```
GET /api/v3/vehicle-maintenance/vehicles/{vin}
```

Wartungseinstellungen, Historie und nächster Service.

#### Wartungsbericht

```
GET /api/v3/vehicle-maintenance/vehicles/{vin}/report
```

Detaillierter Wartungsbericht.

### Gesundheit

#### Warnleuchten

```
GET /api/v1/vehicle-health-report/warning-lights/{vin}
```

Aktive Warnleuchten und Gesundheitsstatus.

### Timer

#### Abfahrtstimer

```
GET /api/v1/vehicle-automatization/{vin}/departure/timers?deviceDateTime={url_encoded_datetime}
```

Konfigurierte Abfahrtstimer. `deviceDateTime` im Format `2024-01-15T10:30:00.000000+01:00` (URL-encoded).

---

## POST Endpoints — Aktionen & Steuerung

### S-PIN

#### S-PIN verifizieren

```
POST /api/v1/spin/verify
```

```json
{
  "currentSpin": "1234"
}
```

### Klimaanlage

#### Klimaanlage starten

```
POST /api/v2/air-conditioning/{vin}/start
```

```json
{
  "heaterSource": "ELECTRIC",
  "targetTemperature": {
    "temperatureValue": 21.5,
    "unitInCar": "CELSIUS"
  }
}
```

> Temperatur in 0,5°C-Schritten.

#### Klimaanlage stoppen

```
POST /api/v2/air-conditioning/{vin}/stop
```

Kein Request Body.

#### Lüftung starten

```
POST /api/v2/air-conditioning/{vin}/active-ventilation/start
```

Kein Request Body.

#### Lüftung stoppen

```
POST /api/v2/air-conditioning/{vin}/active-ventilation/stop
```

Kein Request Body.

#### Scheibenheizung starten

```
POST /api/v2/air-conditioning/{vin}/start-window-heating
```

Kein Request Body.

#### Scheibenheizung stoppen

```
POST /api/v2/air-conditioning/{vin}/stop-window-heating
```

Kein Request Body.

### Standheizung

#### Standheizung starten

```
POST /api/v2/air-conditioning/{vin}/auxiliary-heating/start
```

```json
{
  "spin": "1234"
}
```

> Benötigt S-PIN. Optional können weitere Config-Felder (Dauer, Temperatur) übergeben werden.

#### Standheizung stoppen

```
POST /api/v2/air-conditioning/{vin}/auxiliary-heating/stop
```

Kein Request Body.

### Klimaanlage — Einstellungen

#### Klimaanlage ohne externe Stromversorgung

```
POST /api/v2/air-conditioning/{vin}/settings/ac-without-external-power
```

```json
{
  "airConditioningWithoutExternalPowerEnabled": true
}
```

#### Klimaanlage beim Entriegeln

```
POST /api/v2/air-conditioning/{vin}/settings/ac-at-unlock
```

```json
{
  "airConditioningAtUnlockEnabled": true
}
```

#### Scheibenheizung mit Klimaanlage

```
POST /api/v2/air-conditioning/{vin}/settings/windows-heating
```

```json
{
  "windowHeatingEnabled": true
}
```

#### Sitzheizung mit Klimaanlage

```
POST /api/v2/air-conditioning/{vin}/settings/seats-heating
```

```json
{
  "frontLeft": true,
  "frontRight": true
}
```

> Felder variieren je nach Fahrzeugausstattung.

#### Zieltemperatur setzen

```
POST /api/v2/air-conditioning/{vin}/settings/target-temperature
```

```json
{
  "temperatureValue": 22.0,
  "unitInCar": "CELSIUS"
}
```

### Timer

#### Klimaanlagen-Timer setzen

```
POST /api/v2/air-conditioning/{vin}/timers
```

```json
{
  "timers": [
    {
      "id": 1,
      "enabled": true,
      "time": "07:30",
      "recurringOn": {
        "monday": true,
        "tuesday": false
      }
    }
  ]
}
```

#### Standheizungs-Timer setzen

```
POST /api/v2/air-conditioning/{vin}/auxiliary-heating/timers
```

```json
{
  "spin": "1234",
  "timers": [
    {
      "id": 1,
      "enabled": true,
      "time": "07:30",
      "recurringOn": {
        "monday": true
      }
    }
  ]
}
```

> Benötigt S-PIN.

#### Abfahrtstimer setzen

```
POST /api/v1/vehicle-automatization/{vin}/departure/timers
```

```json
{
  "deviceDateTime": "2024-01-15T10:30:00+00:00",
  "timers": [
    {
      "id": 1,
      "enabled": true
    }
  ]
}
```

#### Mindest-Batteriestand für Abfahrtstimer

```
POST /api/v1/vehicle-automatization/{vin}/departure/timers/settings
```

```json
{
  "minimumBatteryStateOfChargeInPercent": 40
}
```

### Laden

#### Laden starten

```
POST /api/v1/charging/{vin}/start
```

Kein Request Body.

#### Laden stoppen

```
POST /api/v1/charging/{vin}/stop
```

Kein Request Body.

#### Lademodus setzen

```
POST /api/v1/charging/{vin}/set-charge-mode
```

```json
{
  "chargeMode": "MANUAL"
}
```

### Fahrzeugzugriff

#### Fahrzeug verriegeln

```
POST /api/v1/vehicle-access/{vin}/lock
```

```json
{
  "currentSpin": "1234"
}
```

> Benötigt S-PIN.

#### Fahrzeug entriegeln

```
POST /api/v1/vehicle-access/{vin}/unlock
```

```json
{
  "currentSpin": "1234"
}
```

> Benötigt S-PIN.

#### Hupen und Blinken

```
POST /api/v1/vehicle-access/{vin}/honk-and-flash
```

```json
{
  "mode": "HONK_AND_FLASH",
  "vehiclePosition": {
    "latitude": 48.1234,
    "longitude": 11.5678
  }
}
```

> `mode` kann `"HONK_AND_FLASH"` oder `"FLASH"` (nur Blinken) sein.

### Fahrzeug aufwecken

```
POST /api/v1/vehicle-wakeup/{vin}?applyRequestLimiter=true
```

Kein Request Body. Maximal 3× pro Tag.

---

## PUT Endpoints — Konfiguration

#### Ladelimit setzen

```
PUT /api/v1/charging/{vin}/set-charge-limit
```

```json
{
  "targetSOCInPercent": 80
}
```

#### Batteriepflege-Modus

```
PUT /api/v1/charging/{vin}/set-care-mode
```

```json
{
  "chargingCareMode": "ACTIVATED"
}
```

> `"ACTIVATED"` oder `"DEACTIVATED"`

#### Automatisches Entriegeln des Ladesteckers

```
PUT /api/v1/charging/{vin}/set-auto-unlock-plug
```

```json
{
  "autoUnlockPlug": "PERMANENT"
}
```

> `"PERMANENT"` oder `"OFF"`

#### Ladestrom setzen

```
PUT /api/v1/charging/{vin}/set-charging-current
```

```json
{
  "chargingCurrent": "MAXIMUM"
}
```

> `"MAXIMUM"` oder `"REDUCED"`

---

## MQTT — Echtzeit-Events

Neben der REST API nutzt MySkoda einen MQTT-Broker für Echtzeit-Updates.

| | |
|---|---|
| **Broker** | `mqtt.messagehub.de` |
| **Port** | `8883` (TLS/SSL) |
| **Keepalive** | 60 Sekunden |

### Operations-Topics

Status-Updates nach ausgeführten Aktionen:

```
air-conditioning/set-air-conditioning-at-unlock
air-conditioning/set-air-conditioning-seats-heating
air-conditioning/set-air-conditioning-timers
air-conditioning/set-air-conditioning-without-external-power
air-conditioning/set-target-temperature
air-conditioning/start-stop-air-conditioning
auxiliary-heating/start-stop-auxiliary-heating
air-conditioning/start-stop-window-heating
air-conditioning/windows-heating
charging/start-stop-charging
charging/update-battery-support
charging/update-auto-unlock-plug
charging/update-care-mode
charging/update-charge-limit
charging/update-charge-mode
charging/update-charging-profiles
charging/update-charging-current
departure/update-departure-timers
departure/update-minimal-soc
vehicle-access/honk-and-flash
vehicle-access/lock-vehicle
vehicle-services-backup/apply-backup
vehicle-wakeup/wakeup
```

### Service-Event-Topics

Zustandsänderungen am Fahrzeug:

```
air-conditioning
charging
departure
vehicle-status/access
vehicle-status/lights
vehicle-status/odometer
```

### Vehicle-Event-Topics

```
vehicle-connection-status-update
vehicle-ignition-status
```

### Account-Event-Topics

```
account-event/privacy
```

---

## Beispiel: Minimaler Python-Client

```python
import aiohttp
import asyncio

BASE = "https://mysmob.api.connect.skoda-auto.cz"


async def main():
    async with aiohttp.ClientSession() as session:
        # Nach erfolgreicher Auth (access_token vorhanden):
        access_token = "..."
        headers = {"Authorization": f"Bearer {access_token}"}

        # 1. Garage abrufen
        async with session.get(
            f"{BASE}/api/v2/garage"
            "?connectivityGenerations=MOD1"
            "&connectivityGenerations=MOD2"
            "&connectivityGenerations=MOD3"
            "&connectivityGenerations=MOD4",
            headers=headers,
        ) as resp:
            garage = await resp.json()
            print("Garage:", garage)

        # 2. VIN aus Garage extrahieren
        vin = garage["vehicles"][0]["vin"]

        # 3. Fahrzeugstatus abrufen
        async with session.get(
            f"{BASE}/api/v2/vehicle-status/{vin}",
            headers=headers,
        ) as resp:
            status = await resp.json()
            print("Status:", status)

        # 4. Klimaanlage auf 22°C starten
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
            print("AC gestartet:", resp.status)

        # 5. Ladestatus prüfen
        async with session.get(
            f"{BASE}/api/v1/charging/{vin}",
            headers=headers,
        ) as resp:
            charging = await resp.json()
            print("Laden:", charging)


asyncio.run(main())
```

---

## Zusammenfassung

| Kategorie | Anzahl |
|---|---|
| Auth-Aufrufe | 5 |
| GET Endpoints | 19 |
| POST Endpoints | 25 |
| PUT Endpoints | 4 |
| **Gesamt** | **53** |
