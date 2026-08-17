"""
DocVerify AI - Centralized Document Types Configuration
"""

DOCUMENT_CONFIGS = {
    "AADHAAR": {
        "display_name": "Aadhaar Card",
        "code": "AADHAAR",
        "keywords": [
            "aadhaar", "uidai", "unique identification", "government of india",
            "vid", "enrolment", "virtual id"
        ],
        "strong_patterns": [
            r"\b\d{4}\s\d{4}\s\d{4}\b",  # Aadhaar number format
        ],
        "expected_fields": [
            "name", "date_of_birth", "gender", "address", "aadhaar_number"
        ],
        "template_dir": "models/templates/aadhaar",
        "features": {
            "qr_available": True,
            "face_available": True
        }
    },
    "PAN": {
        "display_name": "PAN Card",
        "code": "PAN",
        "keywords": [
            "income tax department", "permanent account number", "pan",
            "govt. of india", "father's name", "father"
        ],
        "strong_patterns": [
            r"\b[A-Z]{5}\d{4}[A-Z]\b",  # PAN format
        ],
        "expected_fields": [
            "name", "fathers_name", "date_of_birth", "pan_number"
        ],
        "template_dir": "models/templates/pan",
        "features": {
            "qr_available": True,
            "face_available": True
        }
    },
    "VOTER_ID": {
        "display_name": "Voter ID",
        "code": "VOTER_ID",
        "keywords": [
            "election commission of india", "elector", "epic", "voter"
        ],
        "strong_patterns": [
            r"\b[A-Z]{3}\d{7}\b",  # EPIC format
        ],
        "expected_fields": [
            "name", "guardian_name", "date_of_birth", "epic_number", "address"
        ],
        "template_dir": "models/templates/voter_id",
        "features": {
            "qr_available": False,
            "face_available": True
        }
    },
    "DRIVING_LICENSE": {
        "display_name": "Driving Licence",
        "code": "DRIVING_LICENSE",
        "keywords": [
            "driving licence", "driving license", "transport", "dl"
        ],
        "strong_patterns": [
            r"\b[A-Z]{2}-?\d{2}[A-Z\d]{6,14}\b",  # DL number
        ],
        "expected_fields": [
            "name", "date_of_birth", "dl_number", "address", "issue_date", "validity", "vehicle_class"
        ],
        "template_dir": "models/templates/driving_license",
        "features": {
            "qr_available": True,  # Some smart DLs have QR
            "face_available": True
        }
    },
    "PASSPORT": {
        "display_name": "Passport",
        "code": "PASSPORT",
        "keywords": [
            "passport", "republic of india", "republic of india passport", "p", "mrz"
        ],
        "strong_patterns": [
            r"\b[A-Z]\d{7}\b",  # Passport number
            r"P<IND",          # MRZ common prefix
        ],
        "expected_fields": [
            "name", "passport_number", "date_of_birth", "nationality", 
            "date_of_issue", "date_of_expiry", "sex", "place_of_birth", "mrz_data"
        ],
        "template_dir": "models/templates/passport",
        "features": {
            "qr_available": False,
            "face_available": True
        }
    }
}
