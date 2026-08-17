# DocVerify AI 🛡

**Intelligent Government Document Authentication Platform**

> Academic Project — BE Information Technology Final Year
> AI-assisted risk assessment. Not an official government verification system.

---

## Overview

DocVerify AI is a full-stack, AI-powered platform for analyzing government identity documents. It performs multi-layer forensic analysis including OCR extraction, forgery detection, template matching, QR validation, and authenticity scoring, generating a 0–100 score with a downloadable PDF report.

```
┌─────────────────────────────────────────────────────────┐
│                    DocVerify AI                         │
│                                                         │
│  Browser ──► FastAPI ──► Verification Pipeline         │
│                │                │                       │
│               RAM          ┌───┴────────────────┐      │
│            State Map        │  Preprocessing     │      │
│               │             │  OCR (EasyOCR)     │      │
│         Volatile Reports    │  Classifier        │      │
│           (ReportLab)       │  Forgery (OpenCV)  │      │
│                             │  Template Match    │      │
│                             │  QR Validator      │      │
│                             │  Face Verify (opt) │      │
│                             │  Scoring Engine    │      │
│                             └──────────────────-─┘      │
└─────────────────────────────────────────────────────────┘
```

---

## Features

- 🔐 Secure JWT-based user authentication
- 📤 Document upload (JPG, PNG, PDF) with drag-and-drop
- 🖼 Image preprocessing pipeline (denoise, CLAHE, deskew, sharpen)
- 📝 OCR text extraction with EasyOCR
- 🏷 Document type classification (Aadhaar, PAN, Passport, DL)
- 🧪 Forgery detection (ELA, edge analysis, noise, clone detection)
- 📐 Template matching (ORB + SSIM)
- 📱 QR code validation (OpenCV + pyzbar)
- 🎯 0–100 authenticity scoring with configurable weights
- 📄 Downloadable PDF verification reports
- 🗂 Verification history with filtering
- 🔬 Demo mode for academic demonstrations

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.11 |
| Architecture | 100% Stateless & Privacy-First |
| State Mgmt | In-Memory Volatile Dictionary |
| OCR | EasyOCR |
| CV | OpenCV + Pillow |
| QR | pyzbar + OpenCV |
| PDF | ReportLab (In-Memory BytesIO) |
| Frontend | HTML5 + CSS3 + Vanilla JS + Jinja2 |
| Tests | pytest |
| Deploy | Docker + docker-compose |

---

## Installation (Windows)

### Prerequisites
- Python 3.11+
- Git
- (Optional) PostgreSQL for production use

### Quick Start

```powershell
# 1. Clone / navigate to project
cd "Doc Verify AI"

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
copy .env.example .env

# 5. Start the server
uvicorn app.main:app --reload

# Open: http://localhost:8000
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./docverify.db` | DB connection string |
| `SECRET_KEY` | — | JWT signing key (change in prod!) |
| `DEMO_MODE` | `true` | Enable demo mode and watermark |
| `UPLOAD_DIR` | `uploads` | Directory for uploaded files |
| `REPORT_DIR` | `reports` | Directory for generated PDFs |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum upload size |
| `ENABLE_FACE_VERIFICATION` | `false` | Enable optional face comparison |
| `OCR_GPU` | `false` | Use GPU for EasyOCR |
| `DEBUG` | `false` | Enable debug/reload mode |

---

## Docker Setup

```bash
# Build and start all services
docker compose up --build

# Access at http://localhost:8000
```

---

## API Documentation

FastAPI generates interactive docs automatically:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Key Endpoints

```
POST /api/documents/upload       Upload document (Volatile / Temporary)
GET  /api/documents/             List user's active documents (MemCache)
DELETE /api/documents/{id}       Wipe document from active memory

POST /api/verification/start?doc_id={id}   Start verification
GET  /api/verification/{id}               Get full result
GET  /api/verification/{id}/status        Get status

GET  /api/reports/{verification_id}       Download PDF report
GET  /api/history/                        Get history (filterable)
```

---

## Authenticity Scoring

Scores are calculated from 6 weighted components:

| Component | Weight | Description |
|-----------|--------|-------------|
| OCR Consistency | 15% | Text extraction quality + field completeness |
| Document Classification | 10% | Type detection confidence |
| Forgery Analysis | 30% | ELA + edge + noise + clone detection |
| Template Matching | 20% | ORB/SSIM similarity to reference templates |
| QR Validation | 15% | QR detection + OCR consistency |
| Face Verification | 10% | Optional selfie comparison |

**Verdicts:**
- 90–100: `LIKELY AUTHENTIC`
- 75–89: `AUTHENTICITY UNCERTAIN`
- 50–74: `SUSPICIOUS`
- 0–49: `LIKELY MANIPULATED`

> Face verification weight is dynamically redistributed when disabled.

---

## Adding ML Models

### Document Classifier (CNN/ViT)
Place trained model at `models/document_classifier/model.pt`
Implement `DocumentClassifier.predict(image_path, raw_text)` in `app/services/document_classifier.py`

### Forgery Detector (Deep Learning)
Place trained model at `models/forgery_detector/model.pt`
Override `ForgeryDetector.analyze(image_path)` to use the model

### Reference Templates
Replace placeholder images in `models/templates/`:
- `aadhaar_template.png`
- `pan_template.png`
- `passport_template.png`
- `dl_template.png`

---

## Adding New Document Types

1. Add keywords and patterns to `DOCUMENT_KEYWORDS` in `app/services/document_classifier.py`
2. Add field extraction regex in `app/services/ocr_service.py`
3. Add template image at `models/templates/{type}_template.png`
4. Add to `TEMPLATE_MAP` in `app/services/template_matcher.py`

---

## Running Tests

```powershell
pytest tests/ -v

# Specific test files
pytest tests/test_scoring.py -v
pytest tests/test_auth.py -v
```

---

## Demo Mode

When `DEMO_MODE=true` (default):
- OCR uses demo text when EasyOCR fails to extract content
- Authenticity scores have slight random variation for demonstration
- All results are labelled "DEMO / AI Simulation"
- No real government data is accessed

---

## Project Limitations & Privacy Statements

⚠️ **Important:**

1. This system performs **AI-assisted forensic risk analysis**, NOT official government authentication
2. It does NOT connect to UIDAI, income tax, passport, or any government databases
3. Forgery detection is based on **statistical anomalies**, not absolute proof
4. Template matching uses **placeholder reference images** unless real templates are provided
5. **No data is retained**. To guarantee privacy, DB couplings have been completely severed and file uploads are held only as long as an active session requires them before absolute deletion on the server.

---

## Future Scope

- Vision Transformer-based forgery detection
- Authorized government API integration (UIDAI, DigiLocker)
- Blockchain-based verification audit trail
- Multi-language OCR (Hindi, regional scripts)
- Liveness detection for face verification
- Cloud deployment (AWS/GCP)
- Enterprise admin dashboard
- Human review workflow

---

## Project Structure

```
Doc Verify AI/
├── app/
│   ├── api/           ← REST API routes
│   ├── core/          ← Config, DB, Security
│   ├── models/        ← SQLAlchemy ORM models
│   ├── schemas/       ← Pydantic schemas
│   ├── services/      ← AI services pipeline
│   ├── utils/         ← File, image, masking utils
│   ├── templates/     ← Jinja2 HTML templates
│   └── static/        ← CSS and JS
├── models/templates/  ← Reference template images
├── uploads/           ← Uploaded documents
├── reports/           ← Generated PDF reports
├── tests/             ← Pytest test suite
├── scripts/           ← DB init scripts
├── sample_data/       ← Synthetic demo documents
└── run.py             ← App entry point
```
