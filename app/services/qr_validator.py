"""
DocVerify AI - QR Code Validator
Detects and parses QR codes using OpenCV + pyzbar fallback.
"""
import cv2
import numpy as np
from typing import Optional


class QRValidator:
    """Detects, reads, and validates QR codes in document images."""

    def validate(self, image_path: str, ocr_fields: Optional[dict] = None) -> dict:
        """
        Detect and validate QR code in a document image.
        Returns: {qr_detected, qr_valid, qr_readable, payload, consistency_score, score, note}
        """
        img = cv2.imread(image_path)
        if img is None:
            return self._no_qr("Could not load image")

        # Try OpenCV QR detector first
        payload, bbox = self._opencv_detect(img)

        # Fallback to pyzbar
        if not payload:
            payload, bbox = self._pyzbar_detect(img)

        if not payload:
            return self._no_qr("No QR code detected in document")

        qr_valid = self._validate_payload(payload)

        # Check consistency with OCR fields
        consistency_score = self._check_consistency(payload, ocr_fields or {})

        # Score calculation  
        if qr_valid and consistency_score >= 80:
            score = 90
        elif qr_valid:
            score = 70
        elif payload:
            score = 50
        else:
            score = 30

        return {
            "qr_detected": True,
            "qr_valid": qr_valid,
            "qr_readable": True,
            "payload": payload[:200] if payload else None,  # Truncate for storage
            "consistency_score": consistency_score,
            "score": score,
            "bounding_box": bbox,
            "note": None,
        }

    def _opencv_detect(self, img: np.ndarray):
        """Try OpenCV QRCodeDetector."""
        try:
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(img)
            if data:
                bb = bbox[0].tolist() if bbox is not None else None
                return data, bb
        except Exception:
            pass
        return None, None

    def _pyzbar_detect(self, img: np.ndarray):
        """Try pyzbar as fallback."""
        try:
            from pyzbar import pyzbar
            decoded = pyzbar.decode(img)
            if decoded:
                d = decoded[0]
                payload = d.data.decode("utf-8", errors="replace")
                rect = d.rect
                bbox = [[rect.left, rect.top], [rect.left + rect.width, rect.top],
                        [rect.left + rect.width, rect.top + rect.height], [rect.left, rect.top + rect.height]]
                return payload, bbox
        except Exception:
            pass
        return None, None

    def _validate_payload(self, payload: str) -> bool:
        """Basic payload validation — non-empty, structured data."""
        if not payload or len(payload.strip()) < 3:
            return False
        # Aadhaar QR often contains XML or structured data
        valid_indicators = ["uid", "name", "dob", "yob", "address", "xml", "digitally"]
        payload_lower = payload.lower()
        return any(kw in payload_lower for kw in valid_indicators) or len(payload) > 20

    def _check_consistency(self, payload: str, ocr_fields: dict) -> float:
        """Check if QR payload data is consistent with OCR-extracted fields."""
        if not ocr_fields:
            return 70.0  # No OCR data to compare — neutral score

        payload_lower = payload.lower()
        matches = 0
        checks = 0

        name = ocr_fields.get("name", "")
        if name:
            checks += 1
            name_words = name.lower().split()
            if any(w in payload_lower for w in name_words if len(w) > 2):
                matches += 1

        dob = ocr_fields.get("dob", "")
        if dob:
            checks += 1
            dob_clean = dob.replace("/", "").replace("-", "")
            if dob_clean in payload.replace("/", "").replace("-", ""):
                matches += 1

        if checks == 0:
            return 70.0

        return round((matches / checks) * 100, 1)

    def _no_qr(self, reason: str) -> dict:
        return {
            "qr_detected": False,
            "qr_valid": False,
            "qr_readable": False,
            "payload": None,
            "consistency_score": None,
            "score": 50,  # Neutral — not all docs have QR
            "bounding_box": None,
            "note": reason,
        }


qr_validator = QRValidator()
