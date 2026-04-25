# Raw Network Traces
To be used as reference.

## `api/v1/notifications-subscriptions`
### `PUT`

Used to register an FCM Token so it can later be used during MQTT authentication.

```
PUT https://mysmob.api.connect.skoda-auto.cz/api/v1/notifications-subscriptions/<REDACTED_FCM_TOKEN> HTTP/2.0
traceparent: 00-e873fa90c6b447c496e0eba8f9be879a-7b198bd93821413e-00
x-app-version-name: 8.11.0
x-app-version-code: 260327003
x-app-installation-id: 318f1332-1266-4393-b274-20abae566393
x-app-platform: Android
x-device-language: en
x-device-country: US
user-agent: MySkoda/Android/8.11.0/260327003
authorization: Bearer <REDACTED_MYSKODA_ACCESS_TOKEN>
x-demo-mode: false
content-type: application/json; charset=UTF-8
content-length: 66
accept-encoding: gzip

{"devicePlatform":"ANDROID","appVersion":"8.11.0","language":"en"}

HTTP/2.0 201
cache-control: no-cache, no-store, max-age=0, must-revalidate
pragma: no-cache
expires: 0
x-content-type-options: nosniff
strict-transport-security: max-age=31536000 ; includeSubDomains
x-frame-options: DENY
x-xss-protection: 0
referrer-policy: no-referrer
content-length: 0
traceid: e873fa90c6b447c496e0eba8f9be879a
date: Sun, 19 Apr 2026 14:29:51 GMT
```
