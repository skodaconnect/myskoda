"""Methods for anonymizing data from the API."""

import re

ACCESS_TOKEN = "eyJ0eXAiOiI0ODEyODgzZi05Y2FiLTQwMWMtYTI5OC0wZmEyMTA5Y2ViY2EiLCJhbGciOiJSUzI1NiJ9"  # noqa: S105
USER_ID = "b8bc126c-ee36-402b-8723-2c1c3dff8dec"
VIN = "TMOCKAA0AA000000"
VIN_REGEX = re.compile(r"TMB\w{14}")
ADDRESS = {
    "city": "Example City",
    "street": "Example Avenue",
    "houseNumber": "15",
    "zipCode": "54321",
    "countryCode": "DEU",
}
SERVICE_PARTNER_ID = "DEU11111"
PARTNER_NUMBER = "1111"
PARTNER_NAME = "Example Service Partner"
LOCATION = {
    "latitude": 53.470636,
    "longitude": 9.689872,
}
EMAIL = "user@example.com"
PHONE = "+49 1234 567890"
VEHICLE_NAME = "Example Car"
LICENSE_PLATE = "HH AA 1234"
URL = "https://example.com"
FIRST_NAME = "John"
LAST_NAME = "Dough"
NICKNAME = "Johnny D."
PROFILE_PICTURE_URL = "https://example.com/profile.jpg"
DATE_OF_BIRTH = "2000-01-01"

SERVICE_PARTNER = {
    "name": PARTNER_NAME,
    "partnerNumber": PARTNER_NUMBER,
    "id": SERVICE_PARTNER_ID,
    "contact": {
        "phone": PHONE,
        "url": URL,
        "email": EMAIL,
    },
    "address": ADDRESS,
    "location": LOCATION,
}


def anonymize_info(data: dict) -> dict:
    data["vin"] = VIN
    data["name"] = VEHICLE_NAME
    if "licensePlate" in data:
        data["licensePlate"] = LICENSE_PLATE
    if "servicePartner" in data:
        data["servicePartner"]["servicePartnerId"] = SERVICE_PARTNER_ID
    return data


def anonymize_maintenance(data: dict) -> dict:
    if "preferredServicePartner" in data:
        data["preferredServicePartner"].update(SERVICE_PARTNER)
    if "predictiveMaintenance" in data:
        data["predictiveMaintenance"]["setting"]["email"] = EMAIL
        data["predictiveMaintenance"]["setting"]["phone"] = PHONE
    for booking in data.get("customerService", {}).get("bookingHistory", []):
        booking["servicePartner"].update(SERVICE_PARTNER)
    for booking in data.get("customerService", {}).get("bookingHistory", []):
        booking["servicePartner"].update(SERVICE_PARTNER)
    return data


def anonymize_charging(data: dict) -> dict:
    return data


def anonymize_chargingprofiles(data: dict) -> dict:
    return data


def anonymize_status(data: dict) -> dict:
    return data


def anonymize_air_conditioning(data: dict) -> dict:
    return data


def anonymize_auxiliary_heating(data: dict) -> dict:
    return data


def anonymize_departure_timers(data: dict) -> dict:
    return data


def anonymize_positions(data: dict) -> dict:
    if "positions" in data:
        for position in data["positions"]:
            position["gpsCoordinates"] = LOCATION
            position["address"] = ADDRESS
    return data


def anonymize_driving_range(data: dict) -> dict:
    return data


def anonymize_trip_statistics(data: dict) -> dict:
    return data


def anonymize_health(data: dict) -> dict:
    return data


def anonymize_user(data: dict) -> dict:
    data["email"] = EMAIL
    data["firstName"] = FIRST_NAME
    data["lastName"] = LAST_NAME
    data["nickname"] = NICKNAME
    data["profilePictureUrl"] = PROFILE_PICTURE_URL
    data["dateOfBirth"] = DATE_OF_BIRTH
    data["phone"] = PHONE

    return data


def anonymize_garage_entry(data: dict) -> dict:
    data["vin"] = VIN
    data["name"] = VEHICLE_NAME
    return data


def anonymize_garage(data: dict) -> dict:
    if "vehicles" in data:
        data["vehicles"] = [anonymize_garage_entry(vehicle) for vehicle in data["vehicles"]]
    return data


def anonymize_url(url: str) -> str:
    return VIN_REGEX.sub(VIN, url)
