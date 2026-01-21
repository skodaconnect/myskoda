"""Methods for anonymizing data from the API."""

import datetime
import re

from myskoda.models.air_conditioning import AirConditioning
from myskoda.models.auxiliary_heating import AuxiliaryHeating
from myskoda.models.charging import Charging
from myskoda.models.charging_history import ChargingHistory
from myskoda.models.chargingprofiles import ChargingProfiles
from myskoda.models.common import Address, Coordinates
from myskoda.models.departure import DepartureInfo
from myskoda.models.driving_range import DrivingRange
from myskoda.models.garage import Garage, GarageEntry
from myskoda.models.health import Health
from myskoda.models.info import Info
from myskoda.models.maintenance import (
    Contact,
    Maintenance,
    MaintenanceReport,
    ServicePartner,
)
from myskoda.models.position import ParkingPositionV3, Positions
from myskoda.models.spin import Spin
from myskoda.models.status import Status
from myskoda.models.trip_statistics import SingleTrips, TripStatistics
from myskoda.models.user import User
from myskoda.models.vehicle_connection_status import VehicleConnectionStatus

ACCESS_TOKEN = "eyJ0eXAiOiI0ODEyODgzZi05Y2FiLTQwMWMtYTI5OC0wZmEyMTA5Y2ViY2EiLCJhbGciOiJSUzI1NiJ9"  # noqa: S105
USER_ID = "b8bc126c-ee36-402b-8723-2c1c3dff8dec"
VIN = "TMOCKAA0AA000000"
VIN_REGEX = re.compile(r"TMB\w{14}")
ADDRESS = Address(
    city="Example City",
    street="Example Avenue",
    house_number="15",
    zip_code="54321",
    country_code="DEU",
)
SERVICE_PARTNER_ID = "DEU11111"
PARTNER_NUMBER = "1111"
PARTNER_NAME = "Example Service Partner"
LOCATION = Coordinates(latitude=53.470636, longitude=9.689872)
EMAIL = "user@example.com"
PHONE = "+49 1234 567890"
VEHICLE_NAME = "Example Car"
LICENSE_PLATE = "HH AA 1234"
URL = "https://example.com"
FIRST_NAME = "John"
LAST_NAME = "Dough"
NICKNAME = "Johnny D."
PROFILE_PICTURE_URL = "https://example.com/profile.jpg"
DATE_OF_BIRTH = datetime.date(2000, 1, 1)
CONTACT = Contact(
    phone=PHONE,
    url=URL,
    email=EMAIL,
)
FORMATTED_ADDRESS = "1600 Pennsylvania Ave NW, Washington, DC 20500, USA"
PROFILE_NAME = "Example Profile"


def anonymize_spin(data: Spin) -> Spin:
    """Anonymize Spin object.

    Args:
        data: Spin object

    Returns:
        Spin object
    """
    return data


def anonymize_info(data: Info) -> Info:
    """Anonymize Info object.

    Args:
        data: Info object

    Returns:
        Info object
    """
    data.vin = VIN
    data.name = VEHICLE_NAME
    if data.license_plate:
        data.license_plate = LICENSE_PLATE
    if data.service_partner:
        data.service_partner.id = SERVICE_PARTNER_ID
    return data


def anonymize_maintenancereport(data: MaintenanceReport) -> MaintenanceReport:
    """Anonymize MaintenanceReport object.

    Args:
        data: MaintenanceReport object

    Returns:
        MaintenanceReport object
    """
    return data


def anonymize_servicepartenr(data: ServicePartner) -> ServicePartner:
    """Anonymize ServicePartner object.

    Args:
        data: ServicePartner object

    Returns:
        ServicePartner object
    """
    data.name = PARTNER_NAME
    data.partner_number = PARTNER_NUMBER
    data.id = SERVICE_PARTNER_ID
    data.address = ADDRESS
    data.location = LOCATION
    data.contact = CONTACT
    return data


def anonymize_maintenance(data: Maintenance) -> Maintenance:
    """Anonymize Maintenance object.

    Args:
        data: Maintenance object

    Returns:
        Maintenance object
    """
    if data.preferred_service_partner:
        data.preferred_service_partner = anonymize_servicepartenr(data.preferred_service_partner)

    if data.predictive_maintenance:
        data.predictive_maintenance.setting.email = EMAIL
        data.predictive_maintenance.setting.phone = PHONE

    if data.customer_service:
        for booking in data.customer_service.booking_history:
            booking.service_partner = anonymize_servicepartenr(booking.service_partner)
        for booking in data.customer_service.active_bookings:
            booking.service_partner = anonymize_servicepartenr(booking.service_partner)
    return data


def anonymize_charging(data: Charging) -> Charging:
    """Anonymize Charging object.

    Args:
        data: Charging object

    Returns:
        Charging object
    """
    return data


def anonymize_charginghistory(data: ChargingHistory) -> ChargingHistory:
    """Anonymize ChargingHistory object.

    Args:
        data: ChargingHistory object

    Returns:
        ChargingHistory object
    """
    return data


def anonymize_chargingprofiles(data: ChargingProfiles) -> ChargingProfiles:
    """Anonymize ChargingProfiles object.

    Args:
        data: ChargingProfiles object

    Returns:
        ChargingProfiles object
    """
    if len(data.charging_profiles) >= 1:
        for profile in data.charging_profiles:
            profile.name = PROFILE_NAME
            if profile.location:
                profile.location = LOCATION
    if data.current_vehicle_position_profile:
        data.current_vehicle_position_profile.name = PROFILE_NAME
    return data


def anonymize_status(data: Status) -> Status:
    """Anonymize Status object.

    Args:
        data: Status object

    Returns:
        Status object
    """
    return data


def anonymize_air_conditioning(data: AirConditioning) -> AirConditioning:
    """Anonymize AirConditioning object.

    Args:
        data: AirConditioning object

    Returns:
        AirConditioning object
    """
    return data


def anonymize_auxiliary_heating(data: AuxiliaryHeating) -> AuxiliaryHeating:
    """Anonymize AirConditioning object.

    Args:
        data: AirConditioning object

    Returns:
        AirConditioning object
    """
    return data


def anonymize_departure_timers(data: DepartureInfo) -> DepartureInfo:
    """Anonymize DepartureInfo object.

    Args:
        data: DepartureInfo object

    Returns:
        DepartureInfo object
    """
    return data


def anonymize_positions(data: Positions) -> Positions:
    """Anonymize Positions object.

    Args:
        data: Positions object

    Returns:
        Positions object
    """
    if data.positions:
        for position in data.positions:
            position.gps_coordinates = LOCATION
            position.address = ADDRESS
    return data


def anonymize_parking_position(data: ParkingPositionV3) -> ParkingPositionV3:
    """Anonymize ParkingPositionV3 object.

    Args:
        data: ParkingPositionV3 object

    Returns:
        ParkingPositionV3 object
    """
    if data.parking_position:
        data.parking_position.gps_coordinates = LOCATION
    if data.parking_position.formatted_address:
        data.parking_position.formatted_address = FORMATTED_ADDRESS
    return data


def anonymize_driving_range(data: DrivingRange) -> DrivingRange:
    """Anonymize DrivingRange object.

    Args:
        data: DrivingRange object

    Returns:
        DrivingRange object
    """
    return data


def anonymize_trip_statistics(data: TripStatistics) -> TripStatistics:
    """Anonymize TripStatistics object.

    Args:
        data: TripStatistics object

    Returns:
        TripStatistics object
    """
    return data


def anonymize_single_trip_statistics(data: SingleTrips) -> SingleTrips:
    """Anonymize SingleTrips object.

    Args:
        data: SingleTrips object

    Returns:
        SingleTrips object
    """
    return data


def anonymize_vehicle_connection_status(data: VehicleConnectionStatus) -> VehicleConnectionStatus:
    """Anonymize VehicleConnectionStatus object.

    Args:
        data: VehicleConnectionStatus object

    Returns:
        VehicleConnectionStatus object
    """
    return data


def anonymize_health(data: Health) -> Health:
    """Anonymize Health object.

    Args:
        data: Health object

    Returns:
        Health object
    """
    return data


def anonymize_user(data: User) -> User:
    """Anonymize User object.

    Args:
        data: User object

    Returns:
        User object
    """
    data.email = EMAIL
    data.first_name = FIRST_NAME
    data.last_name = LAST_NAME
    data.nickname = NICKNAME
    data.profile_picture_url = PROFILE_PICTURE_URL
    data.date_of_birth = DATE_OF_BIRTH
    data.phone = PHONE

    return data


def anonymize_garage_entry(data: GarageEntry) -> GarageEntry:
    """Anonymize GarageEntry object.

    Args:
        data: GarageEntry object

    Returns:
        GarageEntry object
    """
    data.vin = VIN
    data.name = VEHICLE_NAME
    return data


def anonymize_garage(data: Garage) -> Garage:
    """Anonymize Garage object.

    Args:
        data: Garage object

    Returns:
        Garage object
    """
    if data.vehicles:
        data.vehicles = [anonymize_garage_entry(vehicle) for vehicle in data.vehicles]
    return data


def anonymize_url(url: str) -> str:
    """Anonymize a VIN found in a URL.

    Args:
        url: input URL string

    Returns:
        str: URL string with any VIN anonymized
    """
    return VIN_REGEX.sub(VIN, url)
