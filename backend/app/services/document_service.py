import os
import re
from urllib.parse import quote

from bson import ObjectId
from fastapi import UploadFile
from gridfs.asynchronous import AsyncGridFSBucket
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import get_settings
from app.core.exceptions import (
    BusinessRuleException,
    DocumentNotFoundException,
    FileValidationException,
    TripNotFoundException,
)
from app.core.logging import get_logger
from app.db.mongo import to_object_id
from app.schemas.document import DocumentRead

logger = get_logger(__name__)

BUCKET = "trip_documents"
FILES = f"{BUCKET}.files"      # GridFS metadata collection
MAX_DOCS_PER_TRIP = 20

# extension -> (content type we trust, leading bytes the file must start with)
# The type comes from this table, never from the client's header, which can be faked.
ALLOWED_TYPES = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".txt": ("text/plain", None),
}


def _bucket(db: AsyncDatabase) -> AsyncGridFSBucket:
    return AsyncGridFSBucket(db, bucket_name=BUCKET)


async def _ensure_trip(db: AsyncDatabase, trip_id: str) -> None:
    if await db["trips"].count_documents({"_id": to_object_id(trip_id)}, limit=1) == 0:
        raise TripNotFoundException(trip_id)


def _clean_filename(raw: str | None) -> str:
    """Strip any path, replace odd characters, cap the length but keep the extension."""
    name = os.path.basename((raw or "").replace("\\", "/")).strip()
    name = re.sub(r"[^\w.\- ()]", "_", name)
    stem, ext = os.path.splitext(name)
    if not stem:
        raise FileValidationException("File name is missing.")
    return stem[:120] + ext


def _to_read(doc: dict) -> DocumentRead:
    return DocumentRead(
        id=str(doc["_id"]),
        filename=doc["filename"],
        size_bytes=doc["length"],
        content_type=doc["metadata"]["content_type"],
        uploaded_at=doc["uploadDate"],
    )


async def _get_file_doc(db: AsyncDatabase, trip_id: str, document_id: str) -> dict:
    # Matching trip_id as well stops a document id from one trip being used on another.
    doc = await db[FILES].find_one(
        {"_id": to_object_id(document_id), "metadata.trip_id": trip_id}
    )
    if doc is None:
        raise DocumentNotFoundException(document_id)
    return doc


async def upload_document(db: AsyncDatabase, trip_id: str, file: UploadFile) -> DocumentRead:
    await _ensure_trip(db, trip_id)

    filename = _clean_filename(file.filename)
    extension = os.path.splitext(filename)[1].lower()
    if extension not in ALLOWED_TYPES:
        raise FileValidationException("Unsupported file type. Allowed: PDF, PNG, JPG, TXT.", 415)
    content_type, magic = ALLOWED_TYPES[extension]

    max_mb = get_settings().max_upload_mb
    limit = max_mb * 1024 * 1024
    data = await file.read(limit + 1)  # read one byte past the limit to detect oversize cheaply
    if len(data) > limit:
        raise FileValidationException(f"File is larger than {max_mb} MB.", 413)
    if not data:
        raise FileValidationException("File is empty.")
    if magic and not data.startswith(magic):
        raise FileValidationException("File content does not match its extension.", 415)

    if await db[FILES].count_documents({"metadata.trip_id": trip_id}) >= MAX_DOCS_PER_TRIP:
        raise BusinessRuleException(f"A trip can hold at most {MAX_DOCS_PER_TRIP} documents.")

    file_id = await _bucket(db).upload_from_stream(
        filename, data, metadata={"trip_id": trip_id, "content_type": content_type}
    )
    logger.info(f"Document stored: {file_id} ({len(data)} bytes) for trip {trip_id}")
    return _to_read(await db[FILES].find_one({"_id": file_id}))


async def list_documents(db: AsyncDatabase, trip_id: str) -> list[DocumentRead]:
    await _ensure_trip(db, trip_id)
    cursor = db[FILES].find({"metadata.trip_id": trip_id}).sort("uploadDate", -1)
    return [_to_read(doc) for doc in await cursor.to_list(length=None)]


async def download_document(db: AsyncDatabase, trip_id: str, document_id: str) -> tuple[DocumentRead, bytes]:
    doc = await _get_file_doc(db, trip_id, document_id)
    stream = await _bucket(db).open_download_stream(doc["_id"])
    return _to_read(doc), await stream.read()


async def delete_document(db: AsyncDatabase, trip_id: str, document_id: str) -> None:
    doc = await _get_file_doc(db, trip_id, document_id)
    await _bucket(db).delete(doc["_id"])
    logger.info(f"Document deleted: {document_id}")


async def delete_all_for_trip(db: AsyncDatabase, trip_id: str) -> None:
    """Called when a trip is deleted so no orphaned files are left in GridFS."""
    bucket = _bucket(db)
    ids: list[ObjectId] = [
        doc["_id"] async for doc in db[FILES].find({"metadata.trip_id": trip_id}, {"_id": 1})
    ]
    for file_id in ids:
        await bucket.delete(file_id)
    if ids:
        logger.info(f"Removed {len(ids)} document(s) of deleted trip {trip_id}")


def content_disposition(filename: str) -> str:
    # RFC 5987 encoding so non-ASCII names survive; "attachment" forces a download, never inline render.
    return f"attachment; filename*=UTF-8''{quote(filename)}"


__all__ = [
    "upload_document",
    "list_documents",
    "download_document",
    "delete_document",
    "delete_all_for_trip",
    "content_disposition",
]