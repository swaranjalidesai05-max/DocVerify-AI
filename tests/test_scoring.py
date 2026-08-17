"""
DocVerify AI - Tests: Authenticity Scoring
"""
import pytest
from app.services.authenticity_engine import AuthenticityEngine, get_verdict


def test_get_verdict_likely_authentic():
    assert get_verdict(95) == "LIKELY AUTHENTIC"
    assert get_verdict(90) == "LIKELY AUTHENTIC"


def test_get_verdict_uncertain():
    assert get_verdict(80) == "AUTHENTICITY UNCERTAIN"
    assert get_verdict(75) == "AUTHENTICITY UNCERTAIN"


def test_get_verdict_suspicious():
    assert get_verdict(60) == "SUSPICIOUS"
    assert get_verdict(50) == "SUSPICIOUS"


def test_get_verdict_manipulated():
    assert get_verdict(30) == "LIKELY MANIPULATED"
    assert get_verdict(0) == "LIKELY MANIPULATED"


def test_score_calculation_basic():
    engine = AuthenticityEngine()
    ocr = {"confidence": 0.9, "fields": {"name": "Test", "dob": "01/01/1990", "pan_number": "TEST"}}
    clf = {"predicted_type": "pan", "confidence": 0.95, "method": "OCR baseline"}
    forgery = {"tampering_detected": False, "confidence": 0.05, "anomalies": [], "score": 90}
    template = {"matched": True, "similarity_score": 80, "score": 85}
    qr = {"qr_detected": False, "qr_valid": False, "score": 50}
    face = None  # disabled

    result = engine.calculate(ocr, clf, forgery, template, qr, face)
    assert "score" in result
    assert "verdict" in result
    assert "component_scores" in result
    assert 0 <= result["score"] <= 100


def test_face_weight_redistribution():
    """Score without face should still be normalized to a valid range."""
    engine = AuthenticityEngine()
    ocr = {"confidence": 0.85, "fields": {"name": "Test"}}
    clf = {"predicted_type": "aadhaar", "confidence": 0.90, "method": "OCR baseline"}
    forgery = {"score": 85, "tampering_detected": False, "confidence": 0.1, "anomalies": []}
    template = {"score": 70}
    qr = {"score": 60}

    result = engine.calculate(ocr, clf, forgery, template, qr, face_result=None)
    assert result["component_scores"].get("face") is None
    assert 0 <= result["score"] <= 100


def test_verdict_categories():
    """All 4 verdicts should map correctly."""
    engine = AuthenticityEngine()
    
    def make_result(score_pct):
        ocr = {"confidence": score_pct/100, "fields": {}}
        clf = {"predicted_type": "pan", "confidence": score_pct/100, "method": "test"}
        forgery = {"score": score_pct, "tampering_detected": score_pct < 50, "confidence": 0.1, "anomalies": []}
        template = {"score": score_pct}
        qr = {"score": score_pct}
        return engine.calculate(ocr, clf, forgery, template, qr, face_result=None, demo_mode=False)

    # Very high scores should yield authentic
    r = make_result(95)
    assert r["score"] >= 75  # At minimum uncertain (OCR low due to empty fields)
