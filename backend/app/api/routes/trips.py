from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.api.deps import get_db
from app.schemas.trip import (
    ActivityCreate,
    ActivityUpdate,
    BudgetSummary,
    DestinationCreate,
    DestinationUpdate,
    TripCreate,
    TripRead,
    TripUpdate,
)
from app.services import trip_service

router = APIRouter()


# ---------- Trips ----------

@router.post("", response_model=TripRead, status_code=201)
async def create_trip_route(payload: TripCreate, db: AsyncDatabase = Depends(get_db)):
    return await trip_service.create_trip(db, payload)


@router.get("", response_model=list[TripRead])
async def list_trips_route(db: AsyncDatabase = Depends(get_db)):
    return await trip_service.list_trips(db)


@router.get("/{trip_id}", response_model=TripRead)
async def get_trip_route(trip_id: str, db: AsyncDatabase = Depends(get_db)):
    return await trip_service.get_trip(db, trip_id)


@router.patch("/{trip_id}", response_model=TripRead)
async def update_trip_route(trip_id: str, payload: TripUpdate, db: AsyncDatabase = Depends(get_db)):
    return await trip_service.update_trip(db, trip_id, payload)


@router.delete("/{trip_id}", status_code=204)
async def delete_trip_route(trip_id: str, db: AsyncDatabase = Depends(get_db)):
    await trip_service.delete_trip(db, trip_id)


@router.get("/{trip_id}/budget", response_model=BudgetSummary)
async def get_budget_route(trip_id: str, db: AsyncDatabase = Depends(get_db)):
    return (await trip_service.get_trip(db, trip_id)).budget


# ---------- Destinations (every mutation returns the full trip, budget included) ----------

@router.post("/{trip_id}/destinations", response_model=TripRead, status_code=201)
async def add_destination_route(
    trip_id: str, payload: DestinationCreate, db: AsyncDatabase = Depends(get_db)
):
    return await trip_service.add_destination(db, trip_id, payload)


@router.patch("/{trip_id}/destinations/{destination_id}", response_model=TripRead)
async def update_destination_route(
    trip_id: str, destination_id: str, payload: DestinationUpdate, db: AsyncDatabase = Depends(get_db)
):
    return await trip_service.update_destination(db, trip_id, destination_id, payload)


@router.delete("/{trip_id}/destinations/{destination_id}", response_model=TripRead)
async def delete_destination_route(
    trip_id: str, destination_id: str, db: AsyncDatabase = Depends(get_db)
):
    return await trip_service.delete_destination(db, trip_id, destination_id)


# ---------- Activities ----------

@router.post("/{trip_id}/activities", response_model=TripRead, status_code=201)
async def add_activity_route(
    trip_id: str, payload: ActivityCreate, db: AsyncDatabase = Depends(get_db)
):
    return await trip_service.add_activity(db, trip_id, payload)


@router.patch("/{trip_id}/activities/{activity_id}", response_model=TripRead)
async def update_activity_route(
    trip_id: str, activity_id: str, payload: ActivityUpdate, db: AsyncDatabase = Depends(get_db)
):
    return await trip_service.update_activity(db, trip_id, activity_id, payload)


@router.delete("/{trip_id}/activities/{activity_id}", response_model=TripRead)
async def delete_activity_route(
    trip_id: str, activity_id: str, db: AsyncDatabase = Depends(get_db)
):
    return await trip_service.delete_activity(db, trip_id, activity_id)