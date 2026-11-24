import datetime as dt

from pydantic import BaseModel, Field, model_validator

TIME_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"  # "HH:MM", 24h


# ---------- Shared building blocks ----------

class PlaceSnapshot(BaseModel):
    """Place details copied into the trip when a destination is added."""

    place_id: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(default="", max_length=400)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    rating: float | None = Field(default=None, ge=0, le=5)
    rating_count: int | None = Field(default=None, ge=0)


# ---------- Requests ----------

class TripCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    start_date: dt.date
    end_date: dt.date
    budget_total: float = Field(default=0, ge=0, le=1_000_000_000)
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")

    @model_validator(mode="after")
    def end_not_before_start(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date.")
        return self


class TripUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    start_date: dt.date | None = None
    end_date: dt.date | None = None
    budget_total: float | None = Field(default=None, ge=0, le=1_000_000_000)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")

    @model_validator(mode="after")
    def check_fields(self):
        # An explicit null is not allowed for any trip field.
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date.")
        return self


class DestinationCreate(BaseModel):
    place: PlaceSnapshot
    notes: str = Field(default="", max_length=1000)


class DestinationUpdate(BaseModel):
    notes: str = Field(max_length=1000)


class ActivityCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    date: dt.date
    start_time: str | None = Field(default=None, pattern=TIME_PATTERN)
    destination_id: str | None = None
    estimated_cost: float = Field(default=0, ge=0, le=10_000_000)
    actual_cost: float | None = Field(default=None, ge=0, le=10_000_000)
    notes: str = Field(default="", max_length=1000)


class ActivityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    date: dt.date | None = None
    start_time: str | None = Field(default=None, pattern=TIME_PATTERN)
    destination_id: str | None = None
    estimated_cost: float | None = Field(default=None, ge=0, le=10_000_000)
    actual_cost: float | None = Field(default=None, ge=0, le=10_000_000)
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def required_fields_not_null(self):
        # start_time, destination_id and actual_cost may be cleared with null; these may not.
        for field in ("title", "date", "estimated_cost", "notes"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")
        return self


# ---------- Responses ----------

class DestinationRead(PlaceSnapshot):
    id: str
    notes: str = ""


class ActivityRead(BaseModel):
    id: str
    title: str
    date: dt.date
    start_time: str | None = None
    destination_id: str | None = None
    estimated_cost: float
    actual_cost: float | None = None
    notes: str = ""


class BudgetSummary(BaseModel):
    budget_total: float
    total_estimated: float
    total_actual: float
    actual_variance: float   # actual minus estimate, only for activities that have an actual
    remaining: float         # budget_total - total_estimated (negative when over)
    percent_used: float      # total_estimated / budget_total * 100 (0 when no budget)
    status: str              # no_budget | on_track | near_limit | over_budget


class TripRead(BaseModel):
    id: str
    name: str
    start_date: dt.date
    end_date: dt.date
    budget_total: float
    currency: str
    destinations: list[DestinationRead]
    activities: list[ActivityRead]
    budget: BudgetSummary
    created_at: dt.datetime
    updated_at: dt.datetime