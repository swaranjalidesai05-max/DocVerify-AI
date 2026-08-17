"""
DocVerify AI - Tests: Auth + Masking + Classification
"""
import pytest
from app.core.security import hash_password, verify_password
from app.utils.masking import mask_aadhaar, mask_pan, mask_passport, mask_fields
from app.services.document_classifier import DocumentClassifier
from app.services.ocr_service import OCRService


# ── Security Tests ──

def test_password_hashing():
    hashed = hash_password("testpassword123")
    assert hashed != "testpassword123"
    assert verify_password("testpassword123", hashed)


def test_wrong_password_fails():
    hashed = hash_password("correctpassword")
    assert not verify_password("wrongpassword", hashed)


# ── Masking Tests ──

def test_mask_aadhaar():
    result = mask_aadhaar("123456789012")
    assert "XXXX" in result
    assert "9012" in result
    assert "123456" not in result


def test_mask_pan():
    result = mask_pan("ABCDE1234F")
    assert "ABCDE" in result
    assert "****" in result
    assert "1234" not in result


def test_mask_passport():
    result = mask_passport("Z1234567")
    assert "****" in result
    assert len(result) >= 6


def test_mask_fields_dict():
    fields = {"name": "Test User", "aadhaar_number": "123456789012", "pan_number": "ABCDE1234F"}
    masked = mask_fields(fields)
    assert masked["name"] == "Test User"
    assert "123456789012" not in masked.get("aadhaar_number", "")
    assert "1234" not in masked.get("pan_number", "")


# ── Document Classifier Tests ──

def test_classify_aadhaar():
    clf = DocumentClassifier()
    text = "Aadhaar\nUnique Identification Authority of India\nName: Test User\n4567 8901 2345"
    result = clf.classify(text)
    assert result["predicted_type"] == "aadhaar"
    assert result["confidence"] > 0.5


def test_classify_pan():
    clf = DocumentClassifier()
    text = "Income Tax Department\nPermanent Account Number\nDEMOX1234D\nFather: John Doe"
    result = clf.classify(text)
    assert result["predicted_type"] == "pan"


def test_classify_unknown():
    clf = DocumentClassifier()
    result = clf.classify("")
    assert result["predicted_type"] == "unknown"


def test_classify_passport():
    clf = DocumentClassifier()
    text = "Passport\nRepublic of India\nMinistry of External Affairs\nZ1234567\nNationality: Indian"
    result = clf.classify(text)
    assert result["predicted_type"] == "passport"


# ── OCR Tests ──

def test_ocr_demo_fields():
    """Test OCR demo fallback returns expected structure."""
    svc = OCRService()
    raw = svc._get_demo_text("pan")
    fields = svc._extract_fields(raw, "pan")
    assert isinstance(fields, dict)


def test_ocr_extract_dob():
    svc = OCRService()
    text = "DOB: 01/01/1990\nName: Demo User"
    dob = svc._extract_dob(text)
    assert dob is not None
    assert "1990" in dob


def test_ocr_extract_pan():
    svc = OCRService()
    text = "PAN: ABCDE1234F\n"
    pan = svc._extract_pan(text)
    assert pan == "ABCDE1234F"


def test_ocr_extract_aadhaar():
    svc = OCRService()
    text = "1234 5678 9012"
    num = svc._extract_aadhaar(text)
    assert num == "123456789012"
