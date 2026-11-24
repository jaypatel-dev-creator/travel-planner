from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.api.deps import get_db
from app.schemas.assistant import (
    ChatRequest,
    ChatResponse,
    ItineraryRequest,
    ItineraryResponse,
)
from app.services import assistant_service

router = APIRouter()


@router.post("/{trip_id}/assistant/itinerary", response_model=ItineraryResponse)
async def generate_itinerary_route(
    trip_id: str, payload: ItineraryRequest, db: AsyncDatabase = Depends(get_db)
):
    return await assistant_service.generate_itinerary(db, trip_id, payload)


@router.post("/{trip_id}/assistant/chat", response_model=ChatResponse)
async def chat_route(trip_id: str, payload: ChatRequest, db: AsyncDatabase = Depends(get_db)):
    return await assistant_service.chat(db, trip_id, payload)