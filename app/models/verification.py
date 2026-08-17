"""DocVerify AI - Verification, Result, Anomaly, Report Models"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, default=0, nullable=True)  # Deprecated
    visitor_id = Column(String(50), nullable=False, index=True, default="anonymous")
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    authenticity_score = Column(Float, nullable=True)
    verdict = Column(String(50), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    is_demo = Column(Boolean, default=False)
    
    # Classification Metadata
    document_type = Column(String(50), nullable=True)
    document_code = Column(String(50), nullable=True)
    classification_confidence = Column(Float, nullable=True)
    classification_method = Column(String(100), nullable=True)

    document = relationship("Document", back_populates="verifications")
    result = relationship("VerificationResult", back_populates="verification", uselist=False, cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="verification", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="verification", uselist=False, cascade="all, delete-orphan")

    @property
    def document_classification(self):
        if not self.document_code:
            return None
        return {
            "document_type": self.document_type,
            "document_code": self.document_code,
            "confidence": self.classification_confidence,
            "method": self.classification_method
        }


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=False)

    # OCR
    ocr_score = Column(Float, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    extracted_fields = Column(JSON, nullable=True)  # dict of field→value
    raw_text = Column(Text, nullable=True)
    doc_type_detected = Column(String(50), nullable=True)
    classification_confidence = Column(Float, nullable=True)
    classification_method = Column(String(100), nullable=True)

    # Forgery
    forgery_score = Column(Float, nullable=True)
    tampering_detected = Column(Boolean, default=False)
    forgery_confidence = Column(Float, nullable=True)

    # Template
    template_score = Column(Float, nullable=True)
    template_similarity = Column(Float, nullable=True)

    # QR
    qr_score = Column(Float, nullable=True)
    qr_detected = Column(Boolean, default=False)
    qr_valid = Column(Boolean, default=False)
    qr_payload = Column(Text, nullable=True)
    qr_consistency = Column(Float, nullable=True)

    # Face
    face_score = Column(Float, nullable=True)
    face_detected = Column(Boolean, default=False)
    face_similarity = Column(Float, nullable=True)
    face_match = Column(Boolean, nullable=True)

    # Component scores (0-100)
    component_scores = Column(JSON, nullable=True)

    verification = relationship("Verification", back_populates="result")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=False)
    anomaly_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH
    confidence = Column(Float, nullable=False)
    explanation = Column(Text, nullable=False)
    region = Column(JSON, nullable=True)  # {x, y, w, h}

    verification = relationship("Verification", back_populates="anomalies")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    verification = relationship("Verification", back_populates="report")
