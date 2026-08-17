"""
DocVerify AI - PDF Report Generator using ReportLab
Generates professional verification reports.
"""
from pathlib import Path
from typing import Optional
from datetime import datetime
import uuid
from app.core.config import settings


class ReportGenerator:
    """Generates professional PDF verification reports using ReportLab."""

    def generate_in_memory(self, verification_data: dict) -> bytes:
        """
        Generate a PDF report entirely in-memory.
        
        Args:
            verification_data: dict with all verification details
        
        Returns: bytes of the generated PDF
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                HRFlowable, KeepTogether
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        except ImportError:
            raise RuntimeError("ReportLab is not installed. Run: pip install reportlab")

        import io
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "DocVerifyTitle",
            parent=styles["Title"],
            fontSize=22,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=4,
            spaceBefore=0,
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            "DocVerifySubtitle",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#4a4a6a"),
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        section_style = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#1a1a2e"),
            spaceBefore=14,
            spaceAfter=6,
            borderPad=4,
        )
        normal = ParagraphStyle(
            "DocNormal",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#333333"),
            spaceAfter=4,
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#888888"),
            alignment=TA_CENTER,
            spaceAfter=4,
        )

        story = []

        # ── Header ──
        story.append(Paragraph("DocVerify AI", title_style))
        story.append(Paragraph("Intelligent Government Document Authentication", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#4361ee")))
        story.append(Spacer(1, 16))
        
        # ── Big Classification Header ──
        doc_type_str = str(verification_data.get("doc_type") or "Unknown Document").upper()
        raw_conf = verification_data.get("classification_confidence")
        if raw_conf is not None:
            conf_str = f"{float(raw_conf):.1f}%"
        else:
            conf_str = "N/A"
            
        story.append(Paragraph("DOCUMENT TYPE DETECTED", subtitle_style))
        story.append(Paragraph(doc_type_str, title_style))
        story.append(Paragraph(f"AI CLASSIFICATION CONFIDENCE: {conf_str}", subtitle_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="60%", thickness=1, color=colors.HexColor("#4361ee")))
        story.append(Spacer(1, 12))

        # ── Summary Table ──
        score = verification_data.get("score", "—")
        verdict = verification_data.get("verdict", "—")
        verdict_color = self._verdict_color(verdict)

        summary_data = [
            ["Verification ID", str(verification_data.get("verification_id", "—"))],
            ["Date & Time", verification_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))],
            ["Authenticity Score", f"{score}/100"],
            ["Final Verdict", verdict],
        ]
        summary_table = Table(summary_data, colWidths=[5*cm, 11*cm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4ff")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1a1a2e")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 6),
            # Verdict row highlight
            ("TEXTCOLOR", (1, 3), (1, 3), colors.HexColor(verdict_color)),
            ("FONTNAME", (1, 3), (1, 3), "Helvetica-Bold"),
            ("FONTSIZE", (1, 3), (1, 3), 11),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 16))
        
        # ── 1. Document Classification ──
        story.append(Paragraph("1. Document Classification Analysis", section_style))
        class_status = "SUPPORTED" if float(verification_data.get("classification_confidence", 0) or 0) >= settings.CLASSIFICATION_CONFIDENCE_SUPPORTED else "UNSUPPORTED"
        class_mode = str(verification_data.get("classification_method", "Hybrid baseline classifier"))
        class_table_data = [
            ["Detected Document Type:", verification_data.get("doc_type", "Unknown Document")],
            ["Classification Confidence:", conf_str],
            ["Classification Method:", class_mode],
            ["Classification Status:", class_status],
        ]
        ctd = Table(class_table_data, colWidths=[6*cm, 10*cm])
        ctd.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(ctd)
        story.append(Spacer(1, 12))

        # ── Extracted Information ──
        fields = verification_data.get("extracted_fields", {})
        if fields:
            doc_type_friendly = verification_data.get("doc_type", "Document").title()
            story.append(Paragraph(f"2. Extracted {doc_type_friendly} Information", section_style))
            field_data = [[Paragraph(k.replace("_", " ").title(), normal),
                           Paragraph(str(v), normal)] for k, v in fields.items() if v]
            if field_data:
                ft = Table(field_data, colWidths=[6*cm, 10*cm])
                ft.setStyle(TableStyle([
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(ft)
                story.append(Spacer(1, 8))

        # ── Component Scores ──
        story.append(Paragraph("3. Verification Component Results", section_style))
        comp_scores = verification_data.get("component_scores", {})
        comp_labels = {
            "ocr": "OCR Text Extraction",
            "classification": "Document Classification",
            "forgery": "Forgery Analysis",
            "template": "Template Matching",
            "qr": "QR Code Validation",
            "face": "Face Verification",
        }
        comp_data = [["Component", "Score", "Status"]]
        for key, label in comp_labels.items():
            val = comp_scores.get(key)
            if val is None:
                comp_data.append([label, "N/A", "Not Performed"])
            else:
                status = "✓ Pass" if val >= 65 else "⚠ Review" if val >= 40 else "✗ Fail"
                comp_data.append([label, f"{val:.0f}/100", status])

        ct = Table(comp_data, colWidths=[9*cm, 3*cm, 4*cm])
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4361ee")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("ALIGN", (1, 1), (2, -1), "CENTER"),
        ]))
        story.append(ct)
        story.append(Spacer(1, 16))

        # ── Detected Anomalies ──
        anomalies = verification_data.get("anomalies", [])
        story.append(Paragraph("4. Detected Anomalies", section_style))
        if not anomalies:
            story.append(Paragraph("No significant anomalies detected.", normal))
        else:
            anom_data = [["Type", "Severity", "Confidence", "Explanation"]]
            for a in anomalies:
                severity_color = {"HIGH": "#e63946", "MEDIUM": "#f4a261", "LOW": "#2a9d8f"}.get(a.get("severity", "LOW"), "#333")
                anom_data.append([
                    a.get("anomaly_type", "—"),
                    a.get("severity", "—"),
                    f"{a.get('confidence', 0)*100:.0f}%",
                    Paragraph(a.get("explanation", "")[:120], normal),
                ])
            at = Table(anom_data, colWidths=[4*cm, 2.5*cm, 2.5*cm, 7*cm])
            at.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e63946")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fff5f5"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(at)
        story.append(Spacer(1, 16))

        # ── Final Assessment ──
        story.append(Paragraph("5. Final Assessment", section_style))
        is_demo = verification_data.get("is_demo", False)
        demo_note = " [DEMO MODE — AI Simulation]" if is_demo else ""
        assessment_text = (
            f"DocVerify AI generated an authenticity score of <b>{score}/100</b> with a verdict of "
            f"<b>{verdict}</b>{demo_note}. "
        )
        if anomalies:
            assessment_text += f"{len(anomalies)} potential anomaly(ies) were identified during analysis. "
        else:
            assessment_text += "No high-confidence manipulation indicators were detected. "
        assessment_text += (
            "This result represents an AI-assisted forensic risk assessment and should NOT be treated as "
            "official government authentication or legal certification of document authenticity."
        )

        # ── VERIFICATION SUMMARY ──
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 16))
        
        story.append(Paragraph("VERIFICATION SUMMARY", ParagraphStyle(
            "SummaryTitle",
            parent=styles["Heading3"],
            fontSize=12,
            textColor=colors.HexColor("#1a1a2e"),
            alignment=TA_CENTER,
            spaceAfter=12,
        )))
        
        high_anom = [a for a in anomalies if a.get("severity") == "HIGH"]
        med_anom = [a for a in anomalies if a.get("severity") == "MEDIUM"]
        low_anom = [a for a in anomalies if a.get("severity") == "LOW"]
        
        summary_text = (
            f"<b>Document Type:</b> {verification_data.get('doc_type', 'Unknown')}<br/>"
            f"<b>Classification Confidence:</b> {conf_str}<br/><br/>"
            f"<b>Authenticity Score:</b> {score}/100<br/>"
            f"<b>Final Verdict:</b> {verdict}<br/><br/>"
            f"High Severity Anomalies: {len(high_anom)}<br/>"
            f"Medium Severity Anomalies: {len(med_anom)}<br/>"
            f"Low Severity Anomalies: {len(low_anom)}"
        )
        
        assessment_style = ParagraphStyle(
            "Assessment",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#1a1a2e"),
            borderColor=colors.HexColor("#4361ee"),
            borderWidth=1,
            borderPad=8,
            backColor=colors.HexColor("#f0f4ff"),
            spaceAfter=12,
        )
        story.append(Paragraph(summary_text, assessment_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(assessment_text, assessment_style))
        story.append(Spacer(1, 8))

        # ── Footer Disclaimer ──
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "DocVerify AI provides an AI-assisted document risk assessment. The detected document type and authenticity score are based on automated image, OCR, template, QR, and forensic analysis. This system does not constitute official government authentication unless connected to an authorized verification service.",
            disclaimer_style,
        ))
        story.append(Paragraph(
            f"DocVerify AI v{settings.APP_VERSION} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}",
            disclaimer_style,
        ))

        doc.build(story)
        return buffer.getvalue()

    def _verdict_color(self, verdict: str) -> str:
        return {
            "LIKELY AUTHENTIC": "#2a9d8f",
            "AUTHENTICITY UNCERTAIN": "#f4a261",
            "SUSPICIOUS": "#e07b39",
            "LIKELY MANIPULATED": "#e63946",
        }.get(verdict, "#333333")




report_generator = ReportGenerator()
