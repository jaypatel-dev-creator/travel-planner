from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongo import get_database


def get_db() -> AsyncDatabase:
    """FastAPI dependency: routes receive the database, never the client."""
    return get_database()