"""DocVerify AI - Document Schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentOut(BaseModel):
    id: int
    original_filename: str
    doc_type: Optional[str]
    file_size: Optional[int]
    upload_time: datetime
    status: str

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    doc_type: Optional[str] = None
