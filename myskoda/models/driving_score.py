"""Models for responses of /v2/vehicle-status/{vin}/driving-score endpoint."""

from dataclasses import dataclass, field
from datetime import date

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class DrivingScoreResult(DataClassORJSONMixin):
    main: int | None = field(default=None, metadata=field_options(alias="main"))
    braking: int | None = field(default=None, metadata=field_options(alias="braking"))
    in_flow: int | None = field(default=None, metadata=field_options(alias="inFlow"))
    acceleration: int | None = field(default=None, metadata=field_options(alias="acceleration"))
    energy_level: int | None = field(default=None, metadata=field_options(alias="energyLevel"))
    favorable_conditions: int | None = field(
        default=None, metadata=field_options(alias="favorableConditions")
    )
    excessive_trip: int | None = field(default=None, metadata=field_options(alias="excessiveTrip"))
    average_consumption: int | None = field(
        default=None, metadata=field_options(alias="averageConsumption")
    )
    main_bonus: int | None = field(default=None, metadata=field_options(alias="mainBonus"))
    mastered: int | None = field(default=None, metadata=field_options(alias="mastered"))


@dataclass
class DrivingScore(DataClassORJSONMixin):
    """Information about driver's driving score."""

    last_calculation_date: date | None = field(
        default=None, metadata=field_options(alias="lastCalculationDate")
    )
    daily_score: DrivingScoreResult | None = field(
        default=None, metadata=field_options(alias="dailyScore")
    )
    weekly_score: DrivingScoreResult | None = field(
        default=None, metadata=field_options(alias="weeklyScore")
    )
    monthly_score: DrivingScoreResult | None = field(
        default=None, metadata=field_options(alias="monthlyScore")
    )
    quarterly_score: DrivingScoreResult | None = field(
        default=None, metadata=field_options(alias="quarterlyScore")
    )
    mastered_total: int | None = field(default=None, metadata=field_options(alias="masteredTotal"))
    max_score: int | None = field(default=None, metadata=field_options(alias="maxScore"))
    braking_bonus: int | None = field(default=None, metadata=field_options(alias="brakingBonus"))
    in_flow_bonus: int | None = field(default=None, metadata=field_options(alias="inFlowBonus"))
    acceleration_bonus: int | None = field(
        default=None, metadata=field_options(alias="accelerationBonus")
    )
    energy_level_bonus: int | None = field(
        default=None, metadata=field_options(alias="energyLevelBonus")
    )
    favorable_conditions_bonus: int | None = field(
        default=None, metadata=field_options(alias="favorableConditionsBonus")
    )
    excessive_trip_bonus: int | None = field(
        default=None, metadata=field_options(alias="excessiveTripBonus")
    )
    average_consumption_bonus: int | None = field(
        default=None, metadata=field_options(alias="averageConsumptionBonus")
    )
