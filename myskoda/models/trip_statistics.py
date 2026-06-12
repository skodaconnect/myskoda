"""Models for responses of api/v1/trip-statistics/{vin}/single-trips."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from .common import BaseResponse


class VehicleType(StrEnum):
    FUEL = "FUEL"
    HYBRID = "HYBRID"
    ELECTRIC = "ELECTRIC"
    GAS = "GAS"


@dataclass
class StatisticsEntry(DataClassORJSONMixin):
    date: date
    average_fuel_consumption: float | None = field(
        default=None, metadata=field_options(alias="averageFuelConsumption")
    )
    average_gas_consumption: float | None = field(
        default=None, metadata=field_options(alias="averageGasConsumption")
    )
    average_speed_in_kmph: int | None = field(
        default=None, metadata=field_options(alias="averageSpeedInKmph")
    )
    average_electric_consumption: float | None = field(
        default=None, metadata=field_options(alias="averageElectricConsumption")
    )
    average_recuperation: float | None = field(
        default=None, metadata=field_options(alias="averageRecuperation")
    )
    average_aux_consumption: float | None = field(
        default=None, metadata=field_options(alias="averageAuxConsumption")
    )
    mileage_in_km: int | None = field(default=None, metadata=field_options(alias="mileageInKm"))
    travel_time_in_min: int | None = field(
        default=None, metadata=field_options(alias="travelTimeInMin")
    )
    trip_ids: list[int] | None = field(default=None, metadata=field_options(alias="tripIds"))


@dataclass
class FuelCost(DataClassORJSONMixin):
    cost: float | None = field(default=None, metadata=field_options(alias="cost"))
    cost_currency: str | None = field(default=None, metadata=field_options(alias="costCurrency"))
    price_per_unit: float | None = field(default=None, metadata=field_options(alias="pricePerUnit"))


@dataclass
class OverallCost(DataClassORJSONMixin):
    total_cost: float | None = field(default=None, metadata=field_options(alias="totalCost"))
    total_cost_currency: str | None = field(
        default=None, metadata=field_options(alias="totalCostCurrency")
    )
    fuel_cost: FuelCost | None = field(default=None, metadata=field_options(alias="fuelCost"))
    cng_cost: FuelCost | None = field(default=None, metadata=field_options(alias="cngCost"))
    electricity_cost: FuelCost | None = field(
        default=None, metadata=field_options(alias="electricityCost")
    )


@dataclass
class TripStatistics(BaseResponse):
    vehicle_type: VehicleType = field(metadata=field_options(alias="vehicleType"))
    detailed_statistics: list[StatisticsEntry] = field(
        metadata=field_options(alias="detailedStatistics")
    )
    overall_average_electric_consumption: float | None = field(
        default=None, metadata=field_options(alias="overallAverageElectricConsumption")
    )
    overall_average_fuel_consumption: float | None = field(
        default=None, metadata=field_options(alias="overallAverageFuelConsumption")
    )
    overall_average_gas_consumption: float | None = field(
        default=None, metadata=field_options(alias="overallAverageGasConsumption")
    )
    overall_average_mileage_in_km: int | None = field(
        default=None, metadata=field_options(alias="overallAverageMileageInKm")
    )
    overall_average_speed_in_kmph: int | None = field(
        default=None, metadata=field_options(alias="overallAverageSpeedInKmph")
    )
    overall_average_travel_time_in_min: int | None = field(
        default=None, metadata=field_options(alias="overallAverageTravelTimeInMin")
    )
    overall_mileage_in_km: int | None = field(
        default=None, metadata=field_options(alias="overallMileageInKm")
    )
    overall_travel_time_in_min: int | None = field(
        default=None, metadata=field_options(alias="overallTravelTimeInMin")
    )
    overall_cost: OverallCost | None = field(
        default=None, metadata=field_options(alias="overallCost")
    )


@dataclass
class Coordinates(DataClassORJSONMixin):
    latitude: float | None = None
    longitude: float | None = None


@dataclass
class Waypoint(DataClassORJSONMixin):
    charged_here: bool | None = field(default=None, metadata=field_options(alias="chargedHere"))
    coordinates: Coordinates | None = None
    formatted_address: str | None = field(
        default=None, metadata=field_options(alias="formattedAddress")
    )
    location_name: str | None = field(default=None, metadata=field_options(alias="locationName"))

    arrival_time: datetime | None = field(default=None, metadata=field_options(alias="arrivalTime"))
    departure_time: datetime | None = field(
        default=None, metadata=field_options(alias="departureTime")
    )

    arrival_state_of_charge_in_percent: int | None = field(
        default=None, metadata=field_options(alias="arrivalStateOfChargeInPercent")
    )
    departure_state_of_charge_in_percent: int | None = field(
        default=None, metadata=field_options(alias="departureStateOfChargeInPercent")
    )

    distance_to_next_waypoint_in_km: int | None = field(
        default=None, metadata=field_options(alias="distanceToNextWaypointInKm")
    )
    time_to_next_waypoint_in_min: int | None = field(
        default=None, metadata=field_options(alias="timeToNextWaypointInMin")
    )


@dataclass
class Trip(DataClassORJSONMixin):
    id: str | None = field(default=None, metadata=field_options(alias="id"))
    start_time: str | None = field(default=None, metadata=field_options(alias="startTime"))
    end_time: str | None = field(default=None, metadata=field_options(alias="endTime"))
    start_mileage_in_km: int | None = field(
        default=None, metadata=field_options(alias="startMileageInKm")
    )
    end_mileage_in_km: int | None = field(
        default=None, metadata=field_options(alias="endMileageInKm")
    )
    mileage_in_km: int | None = field(default=None, metadata=field_options(alias="mileageInKm"))
    travel_time_in_min: int | None = field(
        default=None, metadata=field_options(alias="travelTimeInMin")
    )
    driving_time_in_min: int | None = field(
        default=None, metadata=field_options(alias="drivingTimeInMin")
    )
    average_speed_in_kmph: int | None = field(
        default=None, metadata=field_options(alias="averageSpeedInKmph")
    )
    average_fuel_consumption: float | None = field(
        default=None, metadata=field_options(alias="averageFuelConsumption")
    )
    average_electric_consumption: float | None = field(
        default=None, metadata=field_options(alias="averageElectricConsumption")
    )
    electric_consumption: float | None = field(
        default=None, metadata=field_options(alias="electricConsumption")
    )
    start_battery_state_of_charge_in_percent: int | None = field(
        default=None, metadata=field_options(alias="startBatteryStateOfChargeInPercent")
    )
    end_battery_state_of_charge_in_percent: int | None = field(
        default=None, metadata=field_options(alias="endBatteryStateOfChargeInPercent")
    )
    cost: OverallCost | None = field(default=None, metadata=field_options(alias="cost"))
    start_location_name: str | None = field(
        default=None, metadata=field_options(alias="startLocationName")
    )
    end_location_name: str | None = field(
        default=None, metadata=field_options(alias="endLocationName")
    )
    is_short_trip: bool | None = field(default=None, metadata=field_options(alias="isShortTrip"))
    waypoints: list[Waypoint] | None = field(
        default=None, metadata=field_options(alias="waypoints")
    )

    @property
    def start_time_utc(self) -> datetime | None:
        """Return the trip start datetime in UTC, based on the first waypoint."""
        if not self.waypoints:
            return None

        for waypoint in self.waypoints:
            if waypoint.departure_time:
                return waypoint.departure_time

        return None

    @property
    def end_time_utc(self) -> datetime | None:
        """Return the trip end datetime in UTC, based on the last waypoint."""
        if not self.waypoints:
            return None

        for waypoint in reversed(self.waypoints):
            if waypoint.arrival_time:
                return waypoint.arrival_time

        return None


@dataclass
class DailyTrip(DataClassORJSONMixin):
    date: str
    overall_mileage: int | None = field(
        default=None, metadata=field_options(alias="overallMileage")
    )
    overall_cost: OverallCost | None = field(
        default=None, metadata=field_options(alias="overallCost")
    )
    trips: list[Trip] | None = field(default=None, metadata=field_options(alias="trips"))


@dataclass
class SingleTrips(BaseResponse):
    daily_trips: list[DailyTrip] = field(metadata=field_options(alias="dailyTrips"))
    vehicle_type: VehicleType | None = field(
        default=None, metadata=field_options(alias="vehicleType")
    )
    short_trip_threshold_in_km: int | None = field(
        default=None, metadata=field_options(alias="shortTripThresholdInKm")
    )
    short_trip_threshold_in_mi: int | None = field(
        default=None, metadata=field_options(alias="shortTripThresholdInMi")
    )
