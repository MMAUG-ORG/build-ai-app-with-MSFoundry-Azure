"""Attachment uploads → Azure Blob Storage."""
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import Attachment, get_session
from ..storage import upload_blob

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("")
async def upload(
    ticket_id: int = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    data = await file.read()
    ext = (file.filename or "bin").rsplit(".", 1)[-1]
    blob_name = f"ticket-{ticket_id}/{uuid.uuid4()}.{ext}"
    url = await upload_blob(blob_name, data, file.content_type or "application/octet-stream")
    att = Attachment(
        ticket_id=ticket_id,
        blob_name=blob_name,
        content_type=file.content_type or "application/octet-stream",
    )
    session.add(att)
    await session.commit()
    return {"id": att.id, "blob_name": blob_name, "url": url}
