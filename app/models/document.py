"""DocVerify AI - Document Model"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=0, nullable=True)  # Deprecated
    visitor_id = Column(String(50), nullable=False, index=True, default="anonymous")
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, default=0)
    mime_type = Column(String(100))
    doc_type = Column(String(50))  # aadhaar, pan, passport, dl, unknown
    upload_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="uploaded")  # uploaded, processing, verified, failed

    verifications = relationship("Verification", back_populates="document", cascade="all, delete-orphan")
