from fastapi import APIRouter, Depends, File, Response, UploadFile
from pymongo.asynchronous.database import AsyncDatabase

from app.api.deps import get_db
from app.schemas.document import DocumentRead
from app.services import document_service

router = APIRouter()


@router.post("/{trip_id}/documents", response_model=DocumentRead, status_code=201)
async def upload_document_route(
    trip_id: str,
    file: UploadFile = File(...),
    db: AsyncDatabase = Depends(get_db),
):
    return await document_service.upload_document(db, trip_id, file)


@router.get("/{trip_id}/documents", response_model=list[DocumentRead])
async def list_documents_route(trip_id: str, db: AsyncDatabase = Depends(get_db)):
    return await document_service.list_documents(db, trip_id)


@router.get("/{trip_id}/documents/{document_id}")
async def download_document_route(
    trip_id: str, document_id: str, db: AsyncDatabase = Depends(get_db)
):
    meta, data = await document_service.download_document(db, trip_id, document_id)
    return Response(
        content=data,
        media_type=meta.content_type,
        headers={
            "Content-Disposition": document_service.content_disposition(meta.filename),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete("/{trip_id}/documents/{document_id}", status_code=204)
async def delete_document_route(
    trip_id: str, document_id: str, db: AsyncDatabase = Depends(get_db)
):
    await document_service.delete_document(db, trip_id, document_id)