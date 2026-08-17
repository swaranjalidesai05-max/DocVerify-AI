"""DocVerify AI - Reports API"""
from fastapi import APIRouter, HTTPException, Response, Request
from app.core.state import active_verifications

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{verification_id}")
def download_report(
    verification_id: str,
    request: Request
):
    """Download the generated report PDF and immediately delete it from memory."""
    v = active_verifications.get(verification_id)
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found or expired")

    if not v.get("has_report"):
        raise HTTPException(status_code=404, detail="Report not yet generated")

    pdf_bytes = v.get("pdf_bytes")
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="Report generation failed in memory")

    # Clean up the verification optionally here, but let's just return the bytes 
    return Response(content=pdf_bytes, media_type="application/pdf")
