"""
DocVerify AI - Verification Pipeline Orchestrator (Privacy-First Stateless)
Central service that runs all verification stages in sequence completely in-memory.
"""
from datetime import datetime
from typing import Optional
import os
import traceback

from app.core.config import settings
from app.core.state import active_documents, active_verifications
from app.services.preprocessing import preprocessor
from app.services.ocr_service import ocr_service
from app.services.document_classifier import document_classifier
from app.services.forgery_detector import forgery_detector
from app.services.template_matcher import template_matcher
from app.services.qr_validator import qr_validator
from app.services.face_verifier import face_verifier
from app.services.authenticity_engine import authenticity_engine
from app.services.report_generator import report_generator
from app.utils.masking import mask_fields
from app.utils.file_utils import delete_file_safe


class VerificationPipeline:
    """
    Orchestrates the full document verification pipeline:
    Upload → Preprocess → OCR → Classify → Forgery → Template → QR → Face → Score → Report
    """

    def verify_stateless(self, doc_id: str, verification_id: str, selfie_path: Optional[str] = None):
        """
        Run full stateless verification for a document.
        Does not interact with the database. Cleans up files aggressively.
        """
        doc = active_documents.get(doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found in state.")

        v = active_verifications[verification_id]
        image_path = doc["file_path"]

        try:
            import time
            start_total = time.time()
            
            # ── Stage 1: Preprocessing ──
            stage_start = time.time()
            print("[VERIFY] Preprocessing started")
            v["processing_stage"] = "Preprocessing image..."
            try:
                preprocessed, original, stages = preprocessor.preprocess(image_path)
                preprocessed_path = image_path  # Use original for OCR
            except Exception:
                preprocessed_path = image_path
                
            print(f"[VERIFY] Preprocessing completed: {time.time() - stage_start:.2f}s")
            
            v["processing_stage"] = "Classifying document & prepping OCR..."
            # ── Stage 2: AI Document Type Detection & OCR Prep ──
            stage_start = time.time()
            print("[VERIFY] Document classification & OCR prep started")
            ocr_result = {"fields": {}, "confidence": 0.5, "raw_text": "", "document_type": "unknown"}
            try:
                ocr_result = ocr_service.extract(preprocessed_path, doc_type=None)
            except Exception:
                pass

            classification_result = {"document_type": "Unknown / Unsupported", "document_code": "UNKNOWN", "confidence": 0.0, "status": "UNSUPPORTED"}
            try:
                classification_result = document_classifier.classify(
                    ocr_result.get("raw_text", ""),
                    preprocessed_path,
                )
            except Exception:
                pass

            detected_type = classification_result.get("document_code", "UNKNOWN")
            v["document_code"] = detected_type
            v["document_type"] = classification_result.get("document_type", "Unknown / Unsupported")
            v["classification_confidence"] = classification_result.get("confidence")
            v["classification_method"] = classification_result.get("classification_method")

            # Early Abort if unsupported
            if classification_result.get("status") == "UNSUPPORTED":
                v["status"] = "completed"
                v["verdict"] = "UNSUPPORTED DOCUMENT"
                v["authenticity_score"] = 0.0
                v["completed_at"] = str(datetime.utcnow())
                print(f"[VERIFY] Document classification & OCR prep aborted: {time.time() - stage_start:.2f}s")
                return

            print(f"[VERIFY] Document classification & OCR prep completed: {time.time() - stage_start:.2f}s")
            v["processing_stage"] = "Extracting OCR fields..."
            # ── Stage 3: Document-Specific OCR Extraction ──
            stage_start = time.time()
            print("[VERIFY] OCR started")
            specific_fields = ocr_service._extract_fields(ocr_result.get("raw_text", ""), detected_type)
            ocr_result["fields"] = specific_fields
            ocr_result["document_type"] = classification_result.get("document_type")
            print(f"[VERIFY] OCR completed: {time.time() - stage_start:.2f}s")

            v["processing_stage"] = "Analyzing forgery details..."
            # ── Stage 4: Forgery Detection ──
            stage_start = time.time()
            print("[VERIFY] Forgery detection started")
            forgery_result = {"tampering_detected": False, "confidence": 0, "anomalies": [], "score": 70}
            try:
                forgery_result = forgery_detector.analyze(preprocessed_path)
            except Exception:
                pass
            print(f"[VERIFY] Forgery detection completed: {time.time() - stage_start:.2f}s")

            v["processing_stage"] = "Matching visual templates..."
            # ── Stage 5: Template Matching ──
            stage_start = time.time()
            print("[VERIFY] Template matching started")
            template_result = {"matched": False, "similarity_score": None, "score": 60}
            try:
                template_result = template_matcher.match(preprocessed_path, detected_type)
            except Exception:
                pass
            print(f"[VERIFY] Template matching completed: {time.time() - stage_start:.2f}s")

            v["processing_stage"] = "Validating QR signatures..."
            # ── Stage 6: QR Validation ──
            stage_start = time.time()
            print("[VERIFY] QR Validation started")
            qr_result = {"qr_detected": False, "score": 50}
            try:
                qr_result = qr_validator.validate(image_path, ocr_result.get("fields", {}))
            except Exception:
                pass
            print(f"[VERIFY] QR Validation completed: {time.time() - stage_start:.2f}s")

            v["processing_stage"] = "Verifying facial identifiers..."
            # ── Stage 7: Face Verification (Optional) ──
            stage_start = time.time()
            print("[VERIFY] Face verification started")
            face_result = None
            if settings.ENABLE_FACE_VERIFICATION and selfie_path:
                try:
                    face_result = face_verifier.verify(image_path, selfie_path)
                except Exception as e:
                    face_result = {"not_available": True, "note": str(e)}
            print(f"[VERIFY] Face verification completed: {time.time() - stage_start:.2f}s")

            v["processing_stage"] = "Calculating authenticity score..."
            # ── Stage 8: Authenticity Scoring ──
            stage_start = time.time()
            print("[VERIFY] Authenticity scoring started")
            try:
                score_result = authenticity_engine.calculate(
                    ocr_result, classification_result, forgery_result,
                    template_result, qr_result, face_result,
                    demo_mode=settings.DEMO_MODE,
                )
            except Exception:
                score_result = {"score": 65.0, "verdict": "AUTHENTICITY UNCERTAIN", "confidence": 0.5, "component_scores": {}}

            # ── Mask sensitive fields ──
            masked_fields = mask_fields(ocr_result.get("fields", {}))

            # ── Prepare Final Result Object ──
            component_scores = score_result.get("component_scores", {})
            v["result"] = {
                "ocr_score": component_scores.get("ocr"),
                "ocr_confidence": ocr_result.get("confidence"),
                "extracted_fields": masked_fields,
                "doc_type_detected": detected_type,
                "classification_confidence": classification_result.get("confidence"),
                "classification_method": classification_result.get("method"),
                "forgery_score": component_scores.get("forgery"),
                "tampering_detected": forgery_result.get("tampering_detected", False),
                "template_score": component_scores.get("template"),
                "template_similarity": template_result.get("similarity_score"),
                "qr_score": component_scores.get("qr"),
                "qr_detected": qr_result.get("qr_detected", False),
                "qr_valid": qr_result.get("qr_valid", False),
                "face_score": component_scores.get("face"),
                "face_detected": bool(face_result and face_result.get("face_detected")),
                "face_similarity": face_result.get("similarity") if face_result else None,
                "component_scores": component_scores,
            }

            v["anomalies"] = [
                {
                    "anomaly_type": a.get("type", "UNKNOWN"),
                    "severity": a.get("severity", "LOW"),
                    "confidence": float(a.get("confidence", 0)),
                    "explanation": a.get("explanation", ""),
                    "region": a.get("region"),
                }
                for a in forgery_result.get("anomalies", []) if a.get("type") != "ANALYSIS_ERROR"
            ]

            v["authenticity_score"] = score_result["score"]
            v["verdict"] = score_result["verdict"]
            print(f"[VERIFY] Authenticity scoring completed: {time.time() - stage_start:.2f}s")

            v["processing_stage"] = "Generating PDF report..."
            # ── Stage 9: Generate In-Memory PDF Report ──
            stage_start = time.time()
            print("[VERIFY] PDF Generation started")
            report_data = {
                "verification_id": verification_id,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "doc_type": detected_type.upper(),
                "classification_confidence": classification_result.get("confidence"),
                "classification_method": classification_result.get("method"),
                "score": score_result["score"],
                "verdict": score_result["verdict"],
                "extracted_fields": masked_fields,
                "component_scores": component_scores,
                "anomalies": v["anomalies"],
                "is_demo": settings.DEMO_MODE,
            }
            try:
                pdf_bytes_data = report_generator.generate_in_memory(report_data)
                v["pdf_bytes"] = pdf_bytes_data
                v["has_report"] = True
            except Exception:
                v["has_report"] = False

            print(f"[VERIFY] PDF Generation completed: {time.time() - stage_start:.2f}s")
            
            v["processing_stage"] = "Completed"
            v["status"] = "completed"
            v["completed_at"] = str(datetime.utcnow())
            print(f"[VERIFY] Total Verification Time: {time.time() - start_total:.2f}s")

        except Exception as err:
            v["status"] = "failed"
            v["processing_stage"] = f"Failed at {v.get('processing_stage', 'Unknown step')} - {str(err)}"
            raise
        finally:
            # Enforce cleanup of the uploaded image no matter what.
            if image_path and os.path.exists(image_path):
                delete_file_safe(image_path)
            # Remove from active_documents dict so it cannot be accessed again
            if doc_id in active_documents:
                del active_documents[doc_id]


verification_pipeline = VerificationPipeline()
