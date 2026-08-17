"""DocVerify AI - File Utilities"""
import os
import uuid
import io
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.core.config import settings


MIME_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "pdf": "application/pdf",
}


def generate_safe_filename(original: str) -> str:
    """Generate a UUID-based safe filename preserving extension."""
    ext = Path(original).suffix.lower().lstrip(".")
    if ext not in settings.allowed_ext_list:
        ext = "bin"
    return f"{uuid.uuid4().hex}.{ext}"


def validate_upload(file: UploadFile, content: bytes) -> str:
    """Validate MIME, extension, and size. Returns extension."""
    original = file.filename or "upload"
    ext = Path(original).suffix.lower().lstrip(".")

    if ext not in settings.allowed_ext_list:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Supported: {', '.join(settings.allowed_ext_list)}"
        )

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max: {settings.MAX_UPLOAD_SIZE_MB} MB"
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    return ext


def save_upload(content: bytes, stored_filename: str) -> Path:
    """Save file bytes to upload directory."""
    dest = settings.upload_path / stored_filename
    dest.write_bytes(content)
    return dest


def delete_file_safe(file_path: str) -> bool:
    """Safely delete a file, returns True if deleted."""
    try:
        p = Path(file_path)
        if p.exists():
            p.unlink()
        return True
    except Exception:
        return False
