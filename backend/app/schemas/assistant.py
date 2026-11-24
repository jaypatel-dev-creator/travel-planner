from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.trip import TripRead


# ---------- What we ask Gemini to return (also used as its JSON schema) ----------

class GeneratedActivity(BaseModel):
    title: str = Field(description="Short activity title, max 120 characters.")
    date: str = Field(description="Date as YYYY-MM-DD, inside the trip dates.")
    start_time: str | None = Field(default=None, description="24h HH:MM, or null if unknown.")
    estimated_cost: float = Field(description="Estimated cost in the trip currency, 0 if free.")
    destination_id: str | None = Field(
        default=None, description="id of one of the trip's destinations, or null."
    )
    notes: str = Field(default="", description="One short practical tip, max 200 characters.")


class GeneratedItinerary(BaseModel):
    activities: list[GeneratedActivity]


# ---------- Requests ----------

class ItineraryRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=500)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=10)


# ---------- Responses ----------

class ChatResponse(BaseModel):
    reply: str


class ItineraryResponse(BaseModel):
    added: int
    skipped: int  # generated activities rejected by server validation (bad date, time, cost...)
    trip: TripRead