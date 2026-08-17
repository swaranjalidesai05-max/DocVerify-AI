"""DocVerify AI - Core Dependencies"""
from fastapi import Request, Response
import uuid

def get_visitor_id(request: Request, response: Response) -> str:
    """FastAPI dependency: get or set anonymous visitor ID."""
    visitor_id = request.cookies.get("visitor_id")
    if not visitor_id:
        visitor_id = str(uuid.uuid4())
        response.set_cookie(
            key="visitor_id",
            value=visitor_id,
            httponly=True,
            max_age=31536000, # 1 year
            samesite="lax",
        )
    return visitor_id
