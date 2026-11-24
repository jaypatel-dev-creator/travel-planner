import uuid
from datetime import datetime, timezone

from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.core.exceptions import (
    ActivityNotFoundException,
    BusinessRuleException,
    DestinationNotFoundException,
    TripNotFoundException,
)
from app.core.logging import get_logger
from app.db.mongo import to_object_id
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
from app.services.budget_service import compute_budget

logger = get_logger(__name__)

COLLECTION = "trips"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


# ---------- Mapping and lookups ----------

def to_trip_read(doc: dict) -> TripRead:
    """Stored document -> API response. Activities come back in timeline order."""
    activities = sorted(
        doc["activities"],
        key=lambda a: (a["date"], a.get("start_time") or "99:99"),  # untimed last in the day
    )
    return TripRead(
        id=str(doc["_id"]),
        name=doc["name"],
        start_date=doc["start_date"],
        end_date=doc["end_date"],
        budget_total=doc["budget_total"],
        currency=doc["currency"],
        destinations=doc["destinations"],
        activities=activities,
        budget=BudgetSummary(**compute_budget(doc["budget_total"], activities)),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


async def _get_doc(db: AsyncDatabase, trip_id: str) -> dict:
    doc = await db[COLLECTION].find_one({"_id": to_object_id(trip_id)})
    if doc is None:
        raise TripNotFoundException(trip_id)
    return doc


async def _raise_missing(db: AsyncDatabase, trip_id: str, child_error: Exception):
    """An update matched nothing: report the trip as missing if it is, else the child."""
    await _get_doc(db, trip_id)
    raise child_error


def _validate_activity_refs(doc: dict, activity_date: str | None, destination_id: str | None) -> None:
    # Dates are stored as ISO strings, which compare correctly as plain strings.
    if activity_date is not None and not (doc["start_date"] <= activity_date <= doc["end_date"]):
        raise BusinessRuleException(
            f"Activity date must be between {doc['start_date']} and {doc['end_date']}."
        )
    if destination_id is not None and not any(d["id"] == destination_id for d in doc["destinations"]):
        raise BusinessRuleException("destination_id does not belong to this trip.")


# ---------- Trips ----------

async def create_trip(db: AsyncDatabase, payload: TripCreate) -> TripRead:
    now = _now()
    doc = {
        **payload.model_dump(mode="json"),
        "destinations": [],
        "activities": [],
        "created_at": now,
        "updated_at": now,
    }
    await db[COLLECTION].insert_one(doc)  # adds _id to doc in place
    logger.info(f"Trip created: {doc['_id']}")
    return to_trip_read(doc)


async def list_trips(db: AsyncDatabase) -> list[TripRead]:
    cursor = db[COLLECTION].find().sort("updated_at", -1).limit(100)
    return [to_trip_read(doc) for doc in await cursor.to_list(length=None)]


async def get_trip(db: AsyncDatabase, trip_id: str) -> TripRead:
    return to_trip_read(await _get_doc(db, trip_id))


async def update_trip(db: AsyncDatabase, trip_id: str, payload: TripUpdate) -> TripRead:
    doc = await _get_doc(db, trip_id)
    changes = payload.model_dump(mode="json", exclude_unset=True)
    if not changes:
        return to_trip_read(doc)

    start = changes.get("start_date", doc["start_date"])
    end = changes.get("end_date", doc["end_date"])
    if end < start:
        raise BusinessRuleException("end_date cannot be before start_date.")

    stranded = [a for a in doc["activities"] if not (start <= a["date"] <= end)]
    if stranded:
        raise BusinessRuleException(
            f"{len(stranded)} activit{'y falls' if len(stranded) == 1 else 'ies fall'} "
            "outside the new dates. Move or delete them first."
        )

    changes["updated_at"] = _now()
    updated = await db[COLLECTION].find_one_and_update(
        {"_id": doc["_id"]}, {"$set": changes}, return_document=ReturnDocument.AFTER
    )
    return to_trip_read(updated)


async def delete_trip(db: AsyncDatabase, trip_id: str) -> None:
    result = await db[COLLECTION].delete_one({"_id": to_object_id(trip_id)})
    if result.deleted_count == 0:
        raise TripNotFoundException(trip_id)
    logger.info(f"Trip deleted: {trip_id}")


# ---------- Destinations ----------

async def add_destination(db: AsyncDatabase, trip_id: str, payload: DestinationCreate) -> TripRead:
    doc = await _get_doc(db, trip_id)
    if any(d["place_id"] == payload.place.place_id for d in doc["destinations"]):
        raise BusinessRuleException(f"'{payload.place.name}' is already in this trip.")

    destination = {"id": _new_id(), **payload.place.model_dump(mode="json"), "notes": payload.notes}
    updated = await db[COLLECTION].find_one_and_update(
        {"_id": doc["_id"]},
        {"$push": {"destinations": destination}, "$set": {"updated_at": _now()}},
        return_document=ReturnDocument.AFTER,
    )
    return to_trip_read(updated)


async def update_destination(
    db: AsyncDatabase, trip_id: str, destination_id: str, payload: DestinationUpdate
) -> TripRead:
    updated = await db[COLLECTION].find_one_and_update(
        {"_id": to_object_id(trip_id), "destinations.id": destination_id},
        {"$set": {"destinations.$[d].notes": payload.notes, "updated_at": _now()}},
        array_filters=[{"d.id": destination_id}],
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        await _raise_missing(db, trip_id, DestinationNotFoundException(destination_id))
    return to_trip_read(updated)


async def delete_destination(db: AsyncDatabase, trip_id: str, destination_id: str) -> TripRead:
    # One atomic update: remove the destination AND unlink activities that pointed at it.
    updated = await db[COLLECTION].find_one_and_update(
        {"_id": to_object_id(trip_id), "destinations.id": destination_id},
        {
            "$pull": {"destinations": {"id": destination_id}},
            "$set": {"activities.$[a].destination_id": None, "updated_at": _now()},
        },
        array_filters=[{"a.destination_id": destination_id}],
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        await _raise_missing(db, trip_id, DestinationNotFoundException(destination_id))
    return to_trip_read(updated)


# ---------- Activities ----------

async def add_activity(db: AsyncDatabase, trip_id: str, payload: ActivityCreate) -> TripRead:
    doc = await _get_doc(db, trip_id)
    activity = {"id": _new_id(), **payload.model_dump(mode="json")}
    _validate_activity_refs(doc, activity["date"], activity["destination_id"])

    updated = await db[COLLECTION].find_one_and_update(
        {"_id": doc["_id"]},
        {"$push": {"activities": activity}, "$set": {"updated_at": _now()}},
        return_document=ReturnDocument.AFTER,
    )
    return to_trip_read(updated)


async def update_activity(
    db: AsyncDatabase, trip_id: str, activity_id: str, payload: ActivityUpdate
) -> TripRead:
    doc = await _get_doc(db, trip_id)
    if not any(a["id"] == activity_id for a in doc["activities"]):
        raise ActivityNotFoundException(activity_id)

    changes = payload.model_dump(mode="json", exclude_unset=True)
    if not changes:
        return to_trip_read(doc)
    _validate_activity_refs(doc, changes.get("date"), changes.get("destination_id"))

    set_ops = {f"activities.$[a].{key}": value for key, value in changes.items()}
    set_ops["updated_at"] = _now()
    updated = await db[COLLECTION].find_one_and_update(
        {"_id": doc["_id"]},
        {"$set": set_ops},
        array_filters=[{"a.id": activity_id}],
        return_document=ReturnDocument.AFTER,
    )
    return to_trip_read(updated)


async def delete_activity(db: AsyncDatabase, trip_id: str, activity_id: str) -> TripRead:
    updated = await db[COLLECTION].find_one_and_update(
        {"_id": to_object_id(trip_id), "activities.id": activity_id},
        {"$pull": {"activities": {"id": activity_id}}, "$set": {"updated_at": _now()}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        await _raise_missing(db, trip_id, ActivityNotFoundException(activity_id))
    return to_trip_read(updated)