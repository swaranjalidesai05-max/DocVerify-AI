"""
DocVerify AI - Authenticity Scoring Engine
Combines all detection component scores into a final 0-100 authenticity score.
Scoring methodology is transparent and configurable.
"""
from typing import Optional


# Default weights (must sum to 1.0 when face is enabled)
BASE_WEIGHTS = {
    "ocr": 0.15,
    "classification": 0.10,
    "forgery": 0.30,
    "template": 0.20,
    "qr": 0.15,
    "face": 0.10,
}

VERDICTS = [
    (90, "LIKELY AUTHENTIC"),
    (75, "AUTHENTICITY UNCERTAIN"),
    (50, "SUSPICIOUS"),
    (0, "LIKELY MANIPULATED"),
]


def get_verdict(score: float) -> str:
    for threshold, verdict in VERDICTS:
        if score >= threshold:
            return verdict
    return "LIKELY MANIPULATED"


class AuthenticityEngine:
    """
    Transparent, configurable authenticity scoring engine.
    
    Combines:
    - OCR consistency score
    - Document classification confidence
    - Forgery detection score
    - Template similarity score  
    - QR validation score
    - Face verification score (optional)
    
    Set DEMO_OFFSET for demo mode to add realistic variation.
    """

    def calculate(
        self,
        ocr_result: dict,
        classification_result: dict,
        forgery_result: dict,
        template_result: dict,
        qr_result: dict,
        face_result: Optional[dict] = None,
        demo_mode: bool = False,
    ) -> dict:
        """
        Calculate final authenticity score.
        Returns: {score, verdict, confidence, component_scores, weights_used}
        """
        # Extract component scores (all 0-100)
        scores = {
            "ocr": self._ocr_score(ocr_result),
            "classification": self._classification_score(classification_result),
            "forgery": self._forgery_score(forgery_result),
            "template": self._template_score(template_result),
            "qr": self._qr_score(qr_result),
            "face": self._face_score(face_result),
        }

        # Build active weights (redistribute face weight if unavailable)
        weights = BASE_WEIGHTS.copy()
        if scores["face"] is None:
            face_w = weights.pop("face")
            total_remaining = sum(weights.values())
            for k in weights:
                weights[k] += face_w * (weights[k] / total_remaining)
        
        # Weighted sum
        active_scores = {k: v for k, v in scores.items() if v is not None}
        weighted_sum = sum(active_scores[k] * weights.get(k, 0) for k in active_scores)
        
        # Normalize (in case weights don't exactly sum to 1 after redistribution)
        total_weight = sum(weights.get(k, 0) for k in active_scores)
        if total_weight > 0:
            final_score = weighted_sum / total_weight
        else:
            final_score = 50.0

        # Demo mode: clamp to reasonable range with slight variation
        if demo_mode:
            import random
            variation = random.uniform(-3, 3)
            final_score = max(55, min(92, final_score + variation))

        final_score = round(final_score, 1)
        verdict = get_verdict(final_score)

        # Confidence reflects agreement between components
        valid_scores = list(active_scores.values())
        if len(valid_scores) >= 2:
            import statistics
            std_dev = statistics.stdev(valid_scores)
            confidence = max(0.5, 1.0 - (std_dev / 100))
        else:
            confidence = 0.7

        return {
            "score": final_score,
            "verdict": verdict,
            "confidence": round(confidence, 3),
            "component_scores": scores,
            "weights_used": {k: round(v, 3) for k, v in weights.items()},
        }

    def _ocr_score(self, r: dict) -> float:
        """Score from OCR results: confidence + field completeness."""
        if not r:
            return 50.0
        conf = r.get("confidence", 0.5) * 100
        fields = r.get("fields", {})
        completeness = min(len(fields) / 3.0, 1.0) * 100
        return round(0.6 * conf + 0.4 * completeness, 1)

    def _classification_score(self, r: dict) -> float:
        if not r:
            return 50.0
        conf = r.get("confidence", 0.5) * 100
        if r.get("predicted_type") == "unknown":
            return max(30.0, conf * 0.5)
        return round(conf, 1)

    def _forgery_score(self, r: dict) -> float:
        if not r:
            return 50.0
        # forgery_result already has a 0-100 score
        return float(r.get("score", 70))

    def _template_score(self, r: dict) -> float:
        if not r:
            return 55.0
        return float(r.get("score", 60))

    def _qr_score(self, r: dict) -> float:
        if not r:
            return 50.0
        return float(r.get("score", 50))

    def _face_score(self, r: Optional[dict]) -> Optional[float]:
        if not r or r.get("not_available"):
            return None
        if not r.get("face_detected"):
            return 40.0
        similarity = r.get("similarity", 50)
        if similarity is None:
            return None
        return round(float(similarity), 1)


authenticity_engine = AuthenticityEngine()
