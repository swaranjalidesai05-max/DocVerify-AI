"""
DocVerify AI - OCR Service using EasyOCR
Extracts structured fields from government documents.
"""
import re
from typing import Optional
from app.core.config import settings
from app.config.document_types import DOCUMENT_CONFIGS

# Lazy-load EasyOCR to avoid startup delay
_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        try:
            import easyocr
            _reader = easyocr.Reader(["en"], gpu=settings.OCR_GPU, verbose=False)
        except Exception as e:
            _reader = None
    return _reader


class OCRService:
    """Extracts text and structured fields from document images."""

    def extract(self, image_path: str, doc_type: Optional[str] = None) -> dict:
        """
        Run OCR on an image and return structured fields.
        Returns: {document_type, fields, raw_text, confidence}
        """
        reader = _get_reader()
        raw_text = ""
        confidence = 0.0

        if reader and not settings.DEMO_MODE:
            try:
                results = reader.readtext(image_path, detail=1, paragraph=False)
                texts = []
                confs = []
                for (bbox, text, conf) in results:
                    texts.append(text)
                    confs.append(conf)
                raw_text = "\n".join(texts)
                confidence = sum(confs) / len(confs) if confs else 0.0
            except Exception as e:
                raw_text = f"[OCR Error: {e}]"
                confidence = 0.0
        else:
            # Demo fallback
            raw_text = self._get_demo_text(doc_type)
            confidence = 0.85

        fields = self._extract_fields(raw_text, doc_type)
        detected_type = doc_type or self._detect_type_from_text(raw_text)

        return {
            "document_type": getattr(doc_type, 'display_name', detected_type),
            "document_code": detected_type,
            "fields": fields,
            "raw_text": raw_text[:2000],  # Limit stored text
            "confidence": round(confidence, 3),
        }

    def _extract_fields(self, text: str, doc_type: Optional[str]) -> dict:
        """Regex-based field extraction from raw OCR text dynamically based on config."""
        fields = {}
        expected = []
        if doc_type and doc_type in DOCUMENT_CONFIGS:
            expected = DOCUMENT_CONFIGS[doc_type].get("expected_fields", [])
        else:
            # If unknown, try to extract everything to be safe or nothing.
            # Best practice: extract basic info anyway if uncertain.
            expected = ["name", "date_of_birth", "aadhaar_number", "pan_number", "passport_number", "dl_number", "epic_number"]

        if "name" in expected:
            n = self._extract_name(text)
            fields["name"] = n if n else "Not detected"
            
        if "date_of_birth" in expected:
            dob = self._extract_dob(text)
            fields["dob"] = dob if dob else "Not detected"
            
        if "gender" in expected:
            g = self._extract_gender(text)
            fields["gender"] = g if g else "Not detected"
            
        if "address" in expected:
            a = self._extract_address_line(text)
            fields["address"] = a if a else "Not detected"
            
        if "aadhaar_number" in expected:
            uid = self._extract_aadhaar(text)
            fields["aadhaar_number"] = uid if uid else "Not detected"
            
        if "pan_number" in expected:
            pan = self._extract_pan(text)
            fields["pan_number"] = pan if pan else "Not detected"
            
        if "passport_number" in expected:
            pp = self._extract_passport(text)
            fields["passport_number"] = pp if pp else "Not detected"
            
        if "dl_number" in expected:
            dl = self._extract_dl(text)
            fields["dl_number"] = dl if dl else "Not detected"
            
        if "epic_number" in expected:
            epic = self._extract_epic(text)
            fields["epic_number"] = epic if epic else "Not detected"
            
        if "nationality" in expected:
            nat = self._extract_nationality(text)
            fields["nationality"] = nat if nat else "Not detected"
            
        if "expiry_date" in expected or "date_of_expiry" in expected:
            exp = self._extract_expiry(text)
            fields["expiry_date"] = exp if exp else "Not detected"
            
        if "validity" in expected:
            val = self._extract_validity(text)
            fields["validity"] = val if val else "Not detected"

        return fields

    def _extract_name(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:Name|NAME)[:\s]+([A-Z][A-Za-z\s]{2,40})",
            r"(?:To|TO)\s+([A-Z][A-Za-z\s]{2,30})",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()
        # Fallback: look for all-caps line that looks like a name
        for line in text.split("\n"):
            line = line.strip()
            if re.match(r"^[A-Z][A-Z\s]{4,30}$", line) and len(line.split()) >= 2:
                return line.title()
        return None

    def _extract_dob(self, text: str) -> Optional[str]:
        m = re.search(r"\b(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})\b", text)
        return m.group(1) if m else None

    def _extract_aadhaar(self, text: str) -> Optional[str]:
        m = re.search(r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b", text)
        if m:
            return m.group(1).replace(" ", "").replace("-", "")
        return None

    def _extract_pan(self, text: str) -> Optional[str]:
        m = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b", text)
        return m.group(1) if m else None

    def _extract_passport(self, text: str) -> Optional[str]:
        m = re.search(r"\b([A-Z][0-9]{7})\b", text)
        return m.group(1) if m else None

    def _extract_dl(self, text: str) -> Optional[str]:
        m = re.search(r"\b([A-Z]{2}\-?\d{2}[A-Z\d]{4,14})\b", text)
        return m.group(1) if m else None

    def _extract_gender(self, text: str) -> Optional[str]:
        m = re.search(r"\b(MALE|FEMALE|Male|Female|M|F)\b", text)
        if m:
            g = m.group(1).upper()
            return "MALE" if g in ("M", "MALE") else "FEMALE"
        return None

    def _extract_expiry(self, text: str) -> Optional[str]:
        m = re.search(r"(?:Expiry|Expiration|Valid until)[:\s]*(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})", text, re.IGNORECASE)
        return m.group(1) if m else None

    def _extract_nationality(self, text: str) -> Optional[str]:
        m = re.search(r"(?:Nationality|NATIONALITY)[:\s]+([A-Z][A-Za-z]+)", text)
        return m.group(1) if m else None

    def _extract_validity(self, text: str) -> Optional[str]:
        m = re.search(r"(?:Valid|Validity|Expiry)[:\s]+(\d{2}[\-/]\d{2}[\-/]\d{4})", text, re.IGNORECASE)
        return m.group(1) if m else None

    def _extract_address_line(self, text: str) -> Optional[str]:
        m = re.search(r"(?:Address|ADDRESS|S/O|D/O|W/O)[:\s]+(.{10,80})", text)
        return m.group(1).strip()[:80] if m else None

    def _extract_epic(self, text: str) -> Optional[str]:
        m = re.search(r"\b([A-Z]{3}\d{7})\b", text)
        return m.group(1) if m else None

    def _detect_type_from_text(self, text: str) -> str:
        text_lower = text.lower()
        for doc_code, config in DOCUMENT_CONFIGS.items():
            if any(kw in text_lower for kw in config["keywords"]):
                return doc_code
        return "UNKNOWN"

    def _get_demo_text(self, doc_type: Optional[str]) -> str:
        demos = {
            "aadhaar": "Government of India\nAadhaar\nUnique Identification Authority of India\nName: DEMO USER\nDOB: 01/01/1990\nMale\n1234 5678 9012\nAddress: 123 Demo Street, Mumbai, Maharashtra - 400001",
            "pan": "Income Tax Department\nPermanent Account Number\nName: DEMO USER\nFather: DEMO FATHER\nDOB: 01/01/1990\nDEMOX1234D",
            "passport": "Republic of India\nPassport\nPassport No: Z1234567\nName: DEMO USER\nNationality: Indian\nDOB: 01/01/1990\nExpiry: 01/01/2030",
            "dl": "Government of India\nDriving Licence\nName: DEMO USER\nDL No: MH-01-20100012345\nDOB: 01/01/1990\nValid: 01/01/2030",
        }
        return demos.get(doc_type, demos["aadhaar"])


ocr_service = OCRService()
