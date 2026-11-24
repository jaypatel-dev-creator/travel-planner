from fastapi import APIRouter, Query

from app.core.exceptions import BusinessRuleException
from app.schemas.place import PlaceSearchResponse
from app.services import places_service

router = APIRouter()


@router.get("/search", response_model=PlaceSearchResponse)
async def search_places_route(q: str = Query(min_length=2, max_length=100)):
    query = q.strip()
    if len(query) < 2:
        raise BusinessRuleException("Search text must be at least 2 characters.")
    return PlaceSearchResponse(results=await places_service.search_places(query))