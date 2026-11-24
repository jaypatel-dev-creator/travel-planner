from bson import ObjectId
from bson.errors import InvalidId
from pymongo import AsyncMongoClient, DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import get_settings
from app.core.exceptions import InvalidIdException
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level singleton. AsyncMongoClient is bound to one event loop,
# so it is created in the app lifespan, not at import time.
_client: AsyncMongoClient | None = None


def init_mongo() -> None:
    global _client
    settings = get_settings()
    _client = AsyncMongoClient(
        settings.mongodb_uri, serverSelectionTimeoutMS=5000, tz_aware=True
    )
    logger.info(f"MongoDB client created - db: {settings.mongodb_db_name}")


def get_database() -> AsyncDatabase:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialised. Call init_mongo() on startup.")
    return _client[get_settings().mongodb_db_name]


async def ensure_indexes() -> None:
    # Trips are listed most-recently-updated first.
    db = get_database()
    await db["trips"].create_index([("updated_at", DESCENDING)])
    await db["trip_documents.files"].create_index("metadata.trip_id")
    logger.info("MongoDB indexes ready.")


async def ping() -> None:
    await get_database().command("ping")


async def close_mongo() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def to_object_id(value: str) -> ObjectId:
    """Convert a path/query id to ObjectId, or raise a 400 instead of a 500."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise InvalidIdException(value)