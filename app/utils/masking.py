"""DocVerify AI - Sensitive Data Masking Utilities"""
import re


def mask_aadhaar(number: str) -> str:
    """Mask Aadhaar: show only last 4 digits. XXXX XXXX 1234"""
    digits = re.sub(r"\D", "", number)
    if len(digits) == 12:
        return f"XXXX XXXX {digits[-4:]}"
    return mask_generic(number, reveal_last=4)


def mask_pan(pan: str) -> str:
    """Mask PAN: ABCDE****F"""
    pan = pan.strip().upper()
    if len(pan) == 10:
        return pan[:5] + "****" + pan[-1]
    return mask_generic(pan, reveal_last=2)


def mask_passport(passport: str) -> str:
    """Mask Passport number: A12****89"""
    if len(passport) >= 6:
        return passport[:2] + "****" + passport[-2:]
    return mask_generic(passport, reveal_last=2)


def mask_dl(dl: str) -> str:
    """Mask Driving License."""
    return mask_generic(dl, reveal_first=4, reveal_last=2)


def mask_generic(value: str, reveal_first: int = 2, reveal_last: int = 2) -> str:
    """Generic masking: show first N and last N chars."""
    if len(value) <= reveal_first + reveal_last:
        return "*" * len(value)
    middle_len = len(value) - reveal_first - reveal_last
    return value[:reveal_first] + "*" * middle_len + value[-reveal_last:]


def mask_fields(fields: dict) -> dict:
    """Auto-mask sensitive fields in an extracted-fields dict."""
    masked = fields.copy()
    mapping = {
        "aadhaar_number": mask_aadhaar,
        "pan_number": mask_pan,
        "passport_number": mask_passport,
        "dl_number": mask_dl,
        "license_number": mask_dl,
    }
    for key, fn in mapping.items():
        if key in masked and masked[key]:
            try:
                masked[key] = fn(str(masked[key]))
            except Exception:
                masked[key] = mask_generic(str(masked[key]))
    return masked
