from pydantic import BaseModel

from app.schemas.trip import PlaceSnapshot


class PlaceSearchResponse(BaseModel):
    results: list[PlaceSnapshot]