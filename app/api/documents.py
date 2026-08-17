"""DocVerify AI - Documents API"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from app.core.state import active_documents
from app.utils.file_utils import generate_safe_filename, validate_upload, save_upload, delete_file_safe
from app.schemas.document import UploadResponse
import uuid
import os

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
):
    """Upload a government identity document anonymously. File stored temporarily."""
    content = await file.read()
    ext = validate_upload(file, content)
    stored_filename = generate_safe_filename(file.filename)
    file_path = save_upload(content, stored_filename)

    doc_id = str(uuid.uuid4())
    
    active_documents[doc_id] = {
        "id": doc_id,
        "original_filename": file.filename,
        "file_path": str(file_path),
        "file_size": len(content),
    }

    return UploadResponse(
        message="Document uploaded successfully. Processing will be temporary.",
        document_id=doc_id,
        filename=file.filename,
    )
