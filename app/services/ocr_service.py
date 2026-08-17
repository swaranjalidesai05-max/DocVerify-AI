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

        if reader:
            try:
                print("[OCR] Extraction started")
                results = reader.readtext(image_path, detail=1, paragraph=False)
                texts = []
                confs = []
                for (bbox, text, conf) in results:
                    texts.append(text)
                    confs.append(conf)
                raw_text = "\n".join(texts)
                confidence = sum(confs) / len(confs) if confs else 0.0
                
                print("[OCR] Extraction completed")
                print(f"[OCR] Number of text regions detected: {len(results)}")
            except Exception as e:
                print(f"[OCR Error] {e}")
                raw_text = ""
                confidence = 0.0
        else:
            print("[OCR Warning] EasyOCR reader not initialized")
            raw_text = ""
            confidence = 0.0

        fields = self._extract_fields(raw_text, doc_type)
        detected_type = doc_type or self._detect_type_from_text(raw_text)

        return {
            "document_type": getattr(doc_type, 'display_name', detected_type) if hasattr(doc_type, 'display_name') else (DOCUMENT_CONFIGS.get(detected_type, {}).get("display_name", detected_type) if detected_type in DOCUMENT_CONFIGS else detected_type),
            "document_code": detected_type,
            "fields": fields,
            "raw_text": raw_text[:2000],  # Limit stored text
            "confidence": round(confidence, 3),
        }

    def _extract_fields(self, text: str, doc_type: Optional[str]) -> dict:
        """Regex-based field extraction from raw OCR text dynamically based on config."""
        if doc_type == "DRIVING_LICENSE":
            res = self._extract_driving_license_fields(text)
            print("[OCR] Field extraction completed")
            return res

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
            fields["date_of_birth"] = dob if dob else "Not detected"
            
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
            
        if "issue_date" in expected:
            issue = self._extract_issue_date(text)
            fields["issue_date"] = issue if issue else "Not detected"
            
        if "validity_nt" in expected:
            val_nt = self._extract_validity_nt(text)
            fields["validity_nt"] = val_nt if val_nt else "Not detected"
            
        if "validity_tr" in expected:
            val_tr = self._extract_validity_tr(text)
            fields["validity_tr"] = val_tr if val_tr else "Not detected"
            
        if "blood_group" in expected:
            bg = self._extract_blood_group(text)
            fields["blood_group"] = bg if bg else "Not detected"
            
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

    def _extract_driving_license_fields(self, text: str) -> dict:
        import re
        from datetime import datetime
        lines = [line.strip() for line in text.split("\n")]
        fields = {
            "name": "Not detected",
            "date_of_birth": "Not detected",
            "dl_number": "Not detected",
            "issue_date": "Not detected",
            "validity_nt": "Not detected",
            "validity_tr": "Not detected",
            "address": "Not detected",
            "blood_group": "Not detected",
            "relative_name": "Not detected"
        }
        
        # 1. DL Number Extraction
        for line in lines:
            m = re.search(r"\b([A-Z]{2}[0-9IOo]{2}\s*\d{11})\b", line, re.IGNORECASE)
            if m:
                # Normalize typical OCR confusion: letter O -> 0 in regional code
                raw_dl = m.group(1)
                # Keep it as is or fix common misread
                fields["dl_number"] = raw_dl
                break
                
        # 2. Date Extraction (DOB, Issue Date, Validity NT, Validity TR)
        all_dates = []
        found_matches = re.findall(r"\b(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})\b", text)
        for date_str in found_matches:
            normalized_str = date_str.replace("/", "-").replace(".", "-")
            try:
                dt = datetime.strptime(normalized_str, "%d-%m-%Y")
                all_dates.append((dt, date_str))
            except ValueError:
                pass
                
        # Remove duplicates
        unique_dates = []
        seen = set()
        for dt, orig in all_dates:
            if dt not in seen:
                seen.add(dt)
                unique_dates.append((dt, orig))
                
        # Sort chronologically
        unique_dates.sort(key=lambda x: x[0])
        
        num_dates = len(unique_dates)
        if num_dates > 0:
            fields["date_of_birth"] = unique_dates[0][1]
            
        if num_dates >= 2:
            fields["validity_tr"] = unique_dates[-1][1]
            
        if num_dates >= 3:
            fields["validity_nt"] = unique_dates[-2][1]
            
        if num_dates == 2:
            fields["issue_date"] = unique_dates[1][1]
        elif num_dates == 3:
            fields["issue_date"] = unique_dates[1][1]
            fields["validity_nt"] = unique_dates[2][1]
        elif num_dates == 4:
            fields["issue_date"] = unique_dates[1][1]
        elif num_dates >= 5:
            fields["issue_date"] = unique_dates[2][1]
            
        # 3. Name Extraction
        for idx, line in enumerate(lines):
            if line.lower() == "name":
                if idx + 2 < len(lines):
                    fields["name"] = lines[idx + 2]
                elif idx + 1 < len(lines):
                    fields["name"] = lines[idx + 1]
                break
                
        # 4. Relative Name Extraction
        for idx, line in enumerate(lines):
            if any(r in line.lower() for r in ["son of", "daughter of", "wife of", "husband of", "father of"]):
                if idx + 2 < len(lines):
                    fields["relative_name"] = lines[idx + 2]
                elif idx + 1 < len(lines):
                    fields["relative_name"] = lines[idx + 1]
                break
                
        # 5. Address Extraction (any line containing a 6-digit number)
        for line in lines:
            if re.search(r"\b\d{6}\b", line):
                fields["address"] = line
                break
                
        # 6. Blood Group Extraction
        for line in lines:
            m = re.match(r"^(A|B|AB|O)[\+\-]$", line, re.IGNORECASE)
            if m:
                fields["blood_group"] = line.upper()
                break
                
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

    def _extract_issue_date(self, text: str) -> Optional[str]:
        m = re.search(r"(?:Issue Date|Date of First Issue|Date of Issue|DOI)[:\s]*(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})", text, re.IGNORECASE)
        return m.group(1) if m else None

    def _extract_validity_nt(self, text: str) -> Optional[str]:
        m = re.search(r"(?:Validity\s+NT|NT|Non[- ]Transport|NT\b)[:\s]*(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})", text, re.IGNORECASE)
        return m.group(1) if m else None

    def _extract_validity_tr(self, text: str) -> Optional[str]:
        m = re.search(r"(?:Validity\s+TR|TR|Transport|\bTR\b)[:\s]*(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})", text, re.IGNORECASE)
        return m.group(1) if m else None

    def _extract_blood_group(self, text: str) -> Optional[str]:
        m = re.search(r"(?:Blood Group|BG)[:\s]*([ABO]{1,2}[\+\-])", text, re.IGNORECASE)
        return m.group(1) if m else None

    def _get_demo_text(self, doc_type: Optional[str]) -> str:
        demos = {
            "aadhaar": "Government of India\nAadhaar\nUnique Identification Authority of India\nName: DEMO USER\nDOB: 01/01/1990\nMale\n1234 5678 9012\nAddress: 123 Demo Street, Mumbai, Maharashtra - 400001",
            "pan": "Income Tax Department\nPermanent Account Number\nName: DEMO USER\nFather: DEMO FATHER\nDOB: 01/01/1990\nDEMOX1234D",
            "passport": "Republic of India\nPassport\nPassport No: Z1234567\nName: DEMO USER\nNationality: Indian\nDOB: 01/01/1990\nExpiry: 01/01/2030",
            "dl": "Government of India\nDriving Licence\nName: DEMO USER\nDOB: 01/01/1990\nLicence Number: MH01 20100012345\nIssue Date: 12-10-2012\nValidity NT: 11-10-2032\nValidity TR: 11-10-2032\nAddress: 123 Demo Street, Mumbai, Maharashtra - 400001\nBlood Group: O+",
        }
        if not doc_type:
            return demos["aadhaar"]
        doc_type_lower = doc_type.lower()
        if "driving" in doc_type_lower or "license" in doc_type_lower or "licence" in doc_type_lower or doc_type_lower == "dl":
            key = "dl"
        elif "aadhaar" in doc_type_lower:
            key = "aadhaar"
        elif "pan" in doc_type_lower:
            key = "pan"
        elif "passport" in doc_type_lower:
            key = "passport"
        else:
            key = doc_type_lower
            
        return demos.get(key, demos["aadhaar"])


ocr_service = OCRService()
