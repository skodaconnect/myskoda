# API endpoints

| Source  | Method | Endpoint                                                                   | Used? | Remarks |
| ------- | ------ | -------------------------------------------------------------------------- | ----- | ------- |
| prior98 | POST   | api/v1/authentication/exchange-authorization-code                          | ✅     |         |
| prior98 | POST   | api/v1/authentication/refresh-token                                        | ✅     |         |
| prior98 | GET    | api/v1/vehicle-health-report/warning-lights/{vin}                          | ✅     |         |
| prior98 | GET    | api/v1/charging/{vin}                                                      | ✅     |         |
| prior98 | GET    | api/v1/maps/positions                                                      | ✅     |         |
| prior98 | GET    | api/v1/trip-statistics/{vin}                                               | ✅     |         |
| prior98 | GET    | api/v1/users                                                               | ✅     |         |
| prior98 | PUT    | api/v1/charging/{vin}/set-care-mode                                        | ✅     |         |
| prior98 | PUT    | api/v1/charging/{vin}/set-charge-limit                                     | ✅     |         |
| prior98 | PUT    | api/v1/charging/{vin}/set-charge-mode                                      | ✅     |         |
| prior98 | POST   | api/v1/charging/{vin}/start                                                | ✅     |         |
| prios98 | POST   | api/v1/charging/{vin}/stop                                                 | ✅     |         |
| prior98 | POST   | api/v1/vehicle-wakeup/{vin}                                                | ✅     |         |
| prior98 | POST   | api/v1/vehicle-access/{vin}/honk-and-flash                                 | ✅     |         |
| sonar98 | POST   | api/v1/users/{user_id}/vehicles/{vin}/check                                |       |         |
| sonar98 | POST   | api/v1/feedbacks                                                           |       |         |
| sonar98 | POST   | api/v1/vehicle-information/{vin}/certificates                              |       |         |
| sonar98 | GET    | api/v1/vehicle-information/{vin}/equipment                                 |       |         |
| sonar98 | GET    | api/v1/vehicle-information/{vin}/certificates/{certificateId}              |       |         |
| sonar98 | GET    | api/v1/ordered-vehicle-information/{commissionId}/equipment                |       |         |
| sonar98 | GET    | api/v1/ordered-vehicle-information/{commissionId}/todos                    |       |         |
| sonar98 | GET    | api/v1/vehicle-information/{vin}                                           |       |         |
| sonar98 | GET    | api/v1/vehicle-information/{vin}/renders                                   |       |         |
| sonar98 | POST   | api/v1/authentication/revoke-token                                         |       |         |
| sonar98 | GET    | api/v1/vehicle-automatization/{vin}/departure/timers                       | ✅      |         |
| sonar98 | POST   | api/v1/vehicle-automatization/{vin}/departure/timers                       | ✅      |         |
| sonar98 | POST   | api/v1/vehicle-automatization/{vin}/departure/timers/settings              |       |         |
| sonar98 | GET    | api/v1/discover-news                                                       |       |         |
| sonar98 | GET    | api/v1/service-partners/{servicePartnerId}/encoded-url                     |       |         |
| sonar98 | GET    | api/v1/service-partners                                                    |       |         |
| sonar98 | POST   | api/v1/maps/places/favourites                                              |       |         |
| sonar98 | DELETE | api/v1/maps/places/favourites/{id}                                         |       |         |
| sonar98 | GET    | api/v1/maps/places/charging-stations                                       |       |         |
| sonar98 | GET    | api/v1/maps/places/favourites                                              |       |         |
| sonar98 | GET    | api/v1/maps/image                                                          |       |         |
| sonar98 | GET    | api/v1/maps/places/{id}                                                    |       |         |
| sonar98 | GET    | api/v1/maps/places/{id}/travel-data                                        |       |         |
| sonar98 | GET    | api/v1/maps/places/predictions                                             |       |         |
| sonar98 | GET    | api/v1/maps/nearby-places                                                  |       |         |
| sonar98 | GET    | api/v1/maps/place                                                          |       |         |
| sonar98 | POST   | api/v1/maps/route                                                          |       |         |
| sonar98 | POST   | api/v1/maps/route-url                                                      |       |         |
| sonar98 | PUT    | api/v1/maps/{vin}/route                                                    |       |         |
| sonar98 | PUT    | api/v1/maps/places/favourites/{id}                                         |       |         |
| sonar98 | POST   | api/v1/vehicle-access/{vin}/lock                                           | ✅      |         |
| sonar98 | POST   | api/v1/vehicle-access/{vin}/unlock                                         | ✅      |         |
| sonar98 | GET    | api/v1/charging/{vin}/certificates                                         |       |         |
| sonar98 | GET    | api/v1/charging/{vin}/profiles                                             |       |         |
| sonar98 | POST   | api/v1/charging/{vin}/certificates/{certificateId}                         |       |         |
| sonar98 | DELETE | api/v1/charging/{vin}/certificates/{certificateId}                         |       |         |
| sonar98 | PUT    | api/v1/charging/{vin}/set-auto-unlock-plug                                 | ✅      |         |
| sonar98 | PUT    | api/v1/charging/{vin}/battery-support                                      |       |         |
| sonar98 | PUT    | api/v1/charging/{vin}/set-charging-current                                 | ✅      |         |
| sonar98 | PUT    | api/v1/charging/{vin}/profiles/{id}                                        |       |         |
| sonar98 | POST   | api/v1/shop/loyalty-products/{productCode}                                 |       |         |
| sonar98 | GET    | api/v1/shop/loyalty-products/{productCode}/image                           |       |         |
| sonar98 | GET    | api/v1/shop/loyalty-products                                               |       |         |
| sonar98 | GET    | api/v1/shop/subscriptions                                                  |       |         |
| sonar98 | GET    | api/v1/shop/cubic-link                                                     |       |         |
| sonar98 | PUT    | api/v1/users/me/account/parking/vehicles                                   |       |         |
| sonar98 | PUT    | api/v1/users/consents/legal-document                                       |       |         |
| sonar98 | PUT    | api/v1/users/consents/marketing                                            |       |         |
| sonar98 | DELETE | api/v1/users/me/account/parking                                            |       |         |
| sonar98 | DELETE | api/v1/users                                                               |       |         |
| sonar98 | GET    | api/v1/users/{id}/identities                                               |       |         |
| sonar98 | GET    | api/v1/users/me/account/parking                                            |       |         |
| sonar98 | GET    | api/v1/users/me/account/parking/summary                                    |       |         |
| sonar98 | GET    | api/v1/users/{id}/profile-picture                                          |       |         |
| sonar98 | GET    | api/v1/users/pay-to-services/supported-countries                           |       |         |
| sonar98 | GET    | api/v1/users/preferences                                                   |       |         |
| sonar98 | GET    | api/v1/users/consents/{consentId}                                          |       |         |
| sonar98 | GET    | api/v1/users/consents                                                      |       |         |
| sonar98 | POST   | api/v1/users/agent-id                                                      |       |         |
| sonar98 | DELETE | api/v1/users/me/account/parking/cards/{cardId}                             |       |         |
| sonar98 | DELETE | api/v1/users/me/account/parking/vehicles/{id}                              |       |         |
| sonar98 | PUT    | api/v1/users/me/account/parking                                            |       |         |
| sonar98 | PATCH  | api/v1/users/me/account/parking/cards/{cardId}                             |       |         |
| sonar98 | PUT    | api/v1/users/consents/{consentId}                                          |       |         |
| sonar98 | PUT    | api/v1/users/preferred-contact-channel                                     |       |         |
| sonar98 | PUT    | api/v1/users/preferences                                                   |       |         |
| sonar98 | GET    | api/v1/notifications                                                       |       |         |
| sonar98 | DELETE | api/v1/parking/sessions/{sessionId}                                        |       |         |
| sonar98 | GET    | api/v1/parking/payment-url                                                 |       |         |
| sonar98 | GET    | api/v1/parking/locations/{locationId}/price                                |       |         |
| sonar98 | GET    | api/v1/parking/sessions/mine                                               |       |         |
| sonar98 | POST   | api/v1/parking/sessions                                                    |       |         |
| sonar98 | POST   | api/v1/vehicle-services-backups/{id}/apply                                 |       |         |
| sonar98 | POST   | api/v1/vehicle-services-backups                                            |       |         |
| sonar98 | DELETE | api/v1/vehicle-services-backups/{id}                                       |       |         |
| sonar98 | GET    | api/v1/vehicle-services-backups                                            |       |         |
| sonar98 | POST   | api/v1/predictive-maintenance/vehicles/{vin}/appointment                   |       |         |
| sonar98 | PUT    | api/v1/predictive-maintenance/vehicles/{vin}/setting                       |       |         |
| sonar98 | PUT    | api/v1/notifications-subscriptions/{id}                                    |       |         |
| sonar98 | GET    | api/v1/notifications-subscriptions/{id}/settings                           |       |         |
| sonar98 | POST   | api/v1/notifications-subscriptions/{id}/settings                           |       |         |
| sonar98 | POST   | api/v1/report                                                              |       |         |
| sonar98 | GET    | api/v1/spin/status                                                         |       |         |
| sonar98 | PUT    | api/v1/spin                                                                |       |         |
| sonar98 | POST   | api/v1/spin                                                                |       |         |
| sonar98 | POST   | api/v1/spin/verify                                                         | ✅      |         |
| sonar98 | POST   | api/v1/trip-statistics/{vin}/fuel-prices                                   |       |         |
| sonar98 | DELETE | api/v1/trip-statistics/{vin}/fuel-prices/{fuelPriceId}                     |       |         |
| sonar98 | PUT    | api/v1/trip-statistics/{vin}/fuel-prices/{fuelPriceId}                     |       |         |
| sonar98 | GET    | api/v1/trip-statistics/{vin}/fuel-prices                                   |       |         |
| EnergyX | GET    | api/v2/car-configurator/url                                                |       |         |
| EnergyX | POST   | api/v2/garage/vehicles/{vin}/capabilities/change-user-capability           |       |         |
| EnergyX | GET    | api/v2/garage/first-vehicle                                                |       |         |
| EnergyX | GET    | api/v2/garage                                                              | ✅      |         |
| EnergyX | GET    | api/v2/garage/initial-vehicle                                              |       |         |
| EnergyX | GET    | api/v2/garage/vehicles/ordered/{commissionId}                              |       |         |
| EnergyX | GET    | api/v2/garage/vehicles/{vin}                                               | ✅      |         |
| EnergyX | GET    | api/v2/garage/vehicles/{vin}/users/guests                                  |       |         |
| EnergyX | GET    | api/v2/garage/vehicles/{vin}/users/guests/count                            |       |         |
| EnergyX | GET    | api/v2/garage/vehicles/{vin}/users/primary                                 |       |         |
| EnergyX | DELETE | api/v2/garage/vehicles/{vin}                                               |       |         |
| EnergyX | DELETE | api/v2/garage/vehicles/{vin}/users/guests/{id}                             |       |         |
| EnergyX | PATCH  | api/v2/garage/vehicles/{vin}                                               |       |         |
| EnergyX | PUT    | api/v2/garage/vehicles/{vin}/license-plate                                 |       |         |
| EnergyX | POST   | api/v2/loyalty-program/members/{id}/rewards                                |       |         |
| EnergyX | POST   | api/v2/loyalty-program/members/{id}/daily-check-in                         |       |         |
| EnergyX | PUT    | api/v2/loyalty-program/members/{id}/challenges/{challengeId}/enrollment    |       |         |
| EnergyX | POST   | api/v2/loyalty-program/members                                             |       |         |
| EnergyX | GET    | api/v2/loyalty-program/members/{id}/challenges                             |       |         |
| EnergyX | GET    | api/v2/loyalty-program/members/{id}                                        |       |         |
| EnergyX | GET    | api/v2/loyalty-program/members/{id}/rewards                                |       |         |
| EnergyX | GET    | api/v2/loyalty-program/members/{id}/transactions                           |       |         |
| EnergyX | GET    | api/v2/loyalty-program/salesforce-contacts/{id}                            |       |         |
| EnergyX | DELETE | api/v2/loyalty-program/members/{id}                                        |       |         |
| EnergyX | DELETE | api/v2/loyalty-program/members/{id}/challenges/{challengeId}/enrollment    |       |         |
| EnergyX | GET    | api/v2/widgets/vehicle-status/{vin}                                        |       |         |
| EnergyX | GET    | api/v2/dealers/{dealerId}                                                  |       |         |
| EnergyX | GET    | api/v2/fueling/sessions/{sessionId}                                        |       |         |
| EnergyX | GET    | api/v2/fueling/sessions/{sessionId}/state                                  |       |         |
| EnergyX | GET    | api/v2/fueling/sessions                                                    |       |         |
| EnergyX | GET    | api/v2/fueling/locations/{locationId}                                      |       |         |
| EnergyX | GET    | api/v2/fueling/sessions/latest                                             |       |         |
| EnergyX | POST   | api/v2/fueling/sessions                                                    |       |         |
| EnergyX | GET    | api/v2/consents/eprivacy/{vin}                                             |       |         |
| EnergyX | GET    | api/v2/consents/location-access                                            |       |         |
| EnergyX | GET    | api/v2/consents/marketing                                                  |       |         |
| EnergyX | GET    | api/v2/consents/terms-of-use                                               |       |         |
| EnergyX | GET    | api/v2/consents/third-party-offers                                         |       |         |
| EnergyX | PATCH  | api/v2/consents/eprivacy/{vin}                                             |       |         |
| EnergyX | PATCH  | api/v2/consents/location-access                                            |       |         |
| EnergyX | PATCH  | api/v2/consents/marketing                                                  |       |         |
| EnergyX | PATCH  | api/v2/consents/third-party-offers                                         |       |         |
| EnergyX | GET    | api/v2/consents/required                                                   |       |         |
| EnergyX | POST   | api/v2/consents                                                            |       |         |
| EnergyX | PUT    | api/v2/consents/{id}                                                       |       |         |
| EnergyX | GET    | api/v2/air-conditioning/{vin}/active-ventilation                           |       |         |
| EnergyX | GET    | api/v2/air-conditioning/{vin}                                              |  ✅     |         |
| EnergyX | GET    | api/v2/air-conditioning/{vin}/auxiliary-heating                            |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/active-ventilation/timers                    |       |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/settings/ac-at-unlock                        |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/settings/seats-heating                       |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/settings/target-temperature                  |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/timers                                       |       |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/settings/windows-heating                     |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/settings/ac-without-external-power           |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/auxiliary-heating/timers                     |       |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/active-ventilation/start                     |       |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/start                                        |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/auxiliary-heating/start                      |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/start-window-heating                         |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/active-ventilation/stop                      |       |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/stop                                         |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/auxiliary-heating/stop                       |  ✅     |         |
| EnergyX | POST   | api/v2/air-conditioning/{vin}/stop-window-heating                          |  ✅     |         |
| EnergyX | POST   | api/v3/maps/places/favourites                                              |       |         |
| EnergyX | DELETE | api/v3/maps/places/favourites/{id}                                         |       |         |
| EnergyX | GET    | api/v3/maps/places/favourites                                              |       |         |
| EnergyX | GET    | api/v3/maps/image                                                          |       |         |
| EnergyX | GET    | api/v3/maps/places/{id}                                                    |       |         |
| EnergyX | POST   | api/v3/maps/nearby-places                                                  |       |         |
| EnergyX | PUT    | api/v3/maps/places/favourites/{id}                                         |       |         |
| EnergyX | POST   | api/v2/maps/route                                                          |       |         |
| EnergyX | GET    | api/v2/maps/charging-stations/{id}/prices                                  |       |         |
| EnergyX | GET    | api/v2/maps/places/{id}                                                    |       |         |
| EnergyX | POST   | api/v2/maps/nearby-places                                                  |       |         |
| EnergyX | PUT    | api/v2/maps/{vin}/route                                                    |       |         |
| EnergyX | GET    | api/v2/manuals/url                                                         |       |         |
| EnergyX | POST   | api/v3/vehicle-maintenance/vehicles/{vin}/service-booking                  |       |         |
| EnergyX | DELETE | api/v3/vehicle-maintenance/vehicles/{vin}/service-partner                  |       |         |
| EnergyX | GET    | api/v3/vehicle-maintenance/service-partners/{servicePartnerId}/encoded-url |       |         |
| EnergyX | GET    | api/v3/vehicle-maintenance/service-partners/{servicePartnerId}             |       |         |
| EnergyX | GET    | api/v3/vehicle-maintenance/service-partners                                |       |         |
| EnergyX | GET    | api/v3/vehicle-maintenance/vehicles/{vin}/report                           |       |         |
| EnergyX | GET    | api/v3/vehicle-maintenance/vehicles/{vin}                                  | ✅      |         |
| EnergyX | PUT    | api/v3/vehicle-maintenance/vehicles/{vin}/service-partner                  |       |         |
| EnergyX | GET    | api/v2/test-drives/dealers                                                 |       |         |
| EnergyX | GET    | api/v2/test-drives/form-definition                                         |       |         |
| EnergyX | GET    | api/v2/vehicle-status/{vin}/driving-range                                  | ✅      |         |
| EnergyX | GET    | api/v2/vehicle-status/render                                               |       |         |
| EnergyX | GET    | api/v2/vehicle-status/{vin}                                                | ✅      |         |
