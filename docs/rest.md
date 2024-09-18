## Unimplemented routes

### Update charging location

**METHOD:** `PUT`
**URL:** `https://mysmob.api.connect.skoda-auto.cz/api/v1/charging/{vin}/profiles/{id}`
**JSON:**

```json
{
    "id": 1,
    "name": "Home",
    "preferredChargingTimes": [
        {
            "enabled": true,
            "endTime": "18:00",
            "id": 1,
            "startTime": "09:00"
        },
        {
            "enabled": false,
            "endTime": "06:00",
            "id": 2,
            "startTime": "22:00"
        },
        {
            "enabled": false,
            "endTime": "06:00",
            "id": 3,
            "startTime": "22:00"
        },
        {
            "enabled": false,
            "endTime": "06:00",
            "id": 4,
            "startTime": "22:00"
        }
    ],
    "settings": {
        "autoUnlockPlugWhenCharged": "PERMANENT",
        "maxChargingCurrent": "MAXIMUM",
        "minBatteryStateOfCharge": {
            "enabled": true,
            "minimumBatteryStateOfChargeInPercent": 40
        },
        "targetStateOfChargeInPercent": 90
    },
    "timers": [
        {
            "enabled": false,
            "id": 1,
            "recurringOn": [
                "MONDAY",
                "TUESDAY",
                "WEDNESDAY",
                "THURSDAY",
                "FRIDAY"
            ],
            "time": "07:00",
            "type": "RECURRING"
        },
        {
            "enabled": false,
            "id": 2,
            "recurringOn": [
                "SATURDAY",
                "SUNDAY"
            ],
            "time": "09:00",
            "type": "RECURRING"
        },
        {
            "enabled": false,
            "id": 3,
            "recurringOn": [
                "MONDAY",
                "TUESDAY",
                "WEDNESDAY",
                "THURSDAY",
                "FRIDAY",
                "SATURDAY",
                "SUNDAY"
            ],
            "time": "07:00",
            "type": "RECURRING"
        }
    ]
}
```

### Get charging locations

**METHOD:** `GET`
**URL:** `https://mysmob.api.connect.skoda-auto.cz/api/v1/charging/{vin}/profiles`
**JSON:**

```json
{
    "carCapturedTimestamp": "2024-09-17T16:12:54.076Z",
    "chargingProfiles": [
        {
            "id": 1,
            "name": "Home",
            "preferredChargingTimes": [
                {
                    "enabled": true,
                    "endTime": "18:00",
                    "id": 1,
                    "startTime": "09:00"
                },
                {
                    "enabled": false,
                    "endTime": "06:00",
                    "id": 2,
                    "startTime": "22:00"
                },
                {
                    "enabled": false,
                    "endTime": "06:00",
                    "id": 3,
                    "startTime": "22:00"
                },
                {
                    "enabled": false,
                    "endTime": "06:00",
                    "id": 4,
                    "startTime": "22:00"
                }
            ],
            "settings": {
                "autoUnlockPlugWhenCharged": "PERMANENT",
                "maxChargingCurrent": "MAXIMUM",
                "minBatteryStateOfCharge": {
                    "minimumBatteryStateOfChargeInPercent": 40
                },
                "targetStateOfChargeInPercent": 90
            },
            "timers": [
                {
                    "enabled": false,
                    "id": 1,
                    "recurringOn": [
                        "MONDAY",
                        "TUESDAY",
                        "WEDNESDAY",
                        "THURSDAY",
                        "FRIDAY"
                    ],
                    "time": "07:00",
                    "type": "RECURRING"
                },
                {
                    "enabled": false,
                    "id": 2,
                    "recurringOn": [
                        "SATURDAY",
                        "SUNDAY"
                    ],
                    "time": "09:00",
                    "type": "RECURRING"
                },
                {
                    "enabled": false,
                    "id": 3,
                    "recurringOn": [
                        "MONDAY",
                        "TUESDAY",
                        "WEDNESDAY",
                        "THURSDAY",
                        "FRIDAY",
                        "SATURDAY",
                        "SUNDAY"
                    ],
                    "time": "07:00",
                    "type": "RECURRING"
                }
            ]
        }
    ]
}
```