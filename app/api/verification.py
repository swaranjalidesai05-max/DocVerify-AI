"""DocVerify AI - Verification API Routes"""
import uuid
import datetime
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from app.core.state import active_verifications, active_documents
from app.services.verification_pipeline import verification_pipeline

router = APIRouter(prefix="/api/verification", tags=["verification"])

@router.post("/start")
def start_verification(
    request: Request,
    doc_id: str,
    background_tasks: BackgroundTasks,
):
    """Start the verification pipeline for an uploaded document."""
    doc = active_documents.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or expired")

    # Prevent duplicate triggers on the same document
    for existing_v in active_verifications.values():
        if existing_v.get("document_id") == doc_id and existing_v.get("status") in ["processing", "completed"]:
            # If already processing, just return its VID
            return {"verification_id": existing_v["verification_id"], "message": "Verification already running", "status": existing_v["status"]}

    vid = str(uuid.uuid4())
    active_verifications[vid] = {
        "verification_id": vid,
        "document_id": doc_id,
        "document_filename": doc.get("original_filename"),
        "status": "processing",
        "processing_stage": "Starting verification...",
        "started_at": str(datetime.datetime.utcnow()),
    }

    try:
        # Run natively in the background
        background_tasks.add_task(verification_pipeline.verify_stateless, doc_id, vid)
        return {"verification_id": vid, "message": "Verification started", "status": "processing"}
    except Exception as e:
        active_verifications[vid]["status"] = "failed"
        active_verifications[vid]["processing_stage"] = "Failed to start pipeline"
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/{verification_id}")
def get_verification(
    verification_id: str,
    request: Request,
):
    """Get full verification result."""
    v = active_verifications.get(verification_id)
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found or expired")

    # The pipeline now directly injects all JSON properties into active_verifications[vid]
    # We will just return it!
    # Hide the raw PDF bytes from JSON API
    response_data = dict(v)
    if "pdf_bytes" in response_data:
        del response_data["pdf_bytes"]
    
    return response_data


@router.get("/{verification_id}/status")
def get_verification_status(
    verification_id: str,
    request: Request,
):
    """Get current status of a verification."""
    v = active_verifications.get(verification_id)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "verification_id": v["verification_id"],
        "status": v.get("status"), 
        "score": v.get("authenticity_score"), 
        "verdict": v.get("verdict")
    }
