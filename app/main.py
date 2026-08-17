"""
DocVerify AI - Main FastAPI Application
"""
from fastapi import FastAPI, Request, Response, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from app.core.config import settings
from app.api import documents, verification, reports
from app.core.dependencies import get_visitor_id
import logging

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Government Document Authentication Platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# API Routers
app.include_router(documents.router)
app.include_router(verification.router)
app.include_router(reports.router)


@app.on_event("startup")
def startup():
    import os
    import shutil
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Demo Mode: {settings.DEMO_MODE}")
    logger.info(f"Privacy-First Architecture Active: Booting Stateless")
    logger.info(f"Cleaning stale temporary files")
    
    # Try one-time stale-file cleanup
    for directory in [settings.UPLOAD_DIR, settings.REPORT_DIR]:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory, ignore_errors=True)
            except BaseException:
                pass
        
        # Re-ensure existence (must not block or loop)
        try:
            os.makedirs(directory, exist_ok=True)
        except BaseException:
            pass
            
    logger.info(f"Temporary cleanup complete")
    logger.info(f"DocVerify AI startup complete - ready to accept requests")

# ── Page Routes ──

@app.get("/health")
def health():
    return {
      "status": "ok",
      "service": "DocVerify AI",
      "mode": "stateless"
    }

@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse("/dashboard")

@app.get("/dashboard")
def dashboard_page(request: Request, response: Response):
    # Stats and recent items are removed, as history is completely stateless.
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "demo_mode": settings.DEMO_MODE,
        },
    )


@app.get("/upload")
def upload_page(request: Request, response: Response):
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={
            "max_size_mb": settings.MAX_UPLOAD_SIZE_MB,
            "allowed_ext": settings.ALLOWED_EXTENSIONS,
        },
    )


@app.get("/verification/{verification_id}")
def verification_result_page(
    verification_id: str,
    request: Request,
    response: Response
):
    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "verification_id": verification_id,
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION, "demo": settings.DEMO_MODE}
