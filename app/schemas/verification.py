"""DocVerify AI - Verification Schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any


class AnomalyOut(BaseModel):
    id: int
    anomaly_type: str
    severity: str
    confidence: float
    explanation: str
    region: Optional[Any] = None

    class Config:
        from_attributes = True


class DocumentClassificationOut(BaseModel):
    document_type: Optional[str]
    document_code: Optional[str]
    confidence: Optional[float]
    method: Optional[str]

    class Config:
        from_attributes = True


class VerificationOut(BaseModel):
    id: int
    document_id: int
    status: str
    document_classification: Optional[DocumentClassificationOut] = None
    authenticity_score: Optional[float]
    verdict: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    is_demo: bool

    class Config:
        from_attributes = True


class HistoryItem(BaseModel):
    verification_id: int
    document_filename: str
    doc_type: Optional[str]
    authenticity_score: Optional[float]
    verdict: Optional[str]
    started_at: datetime
    status: str
    has_report: bool
