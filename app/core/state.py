"""
DocVerify AI - In-Memory State Management
Replaces database for temporary verification tracking.
"""
from typing import Dict, Any

# UUID -> dict containing verification data
# Data cascades out of memory either automatically on TTL or upon extraction
active_verifications: Dict[str, Any] = {}
active_documents: Dict[str, Any] = {}
