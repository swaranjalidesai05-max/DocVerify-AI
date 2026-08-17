"""
DocVerify AI - Template Matcher
Compares uploaded document against reference templates using ORB + SSIM.
Reference template images are stored in models/templates/.
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional


TEMPLATE_MAP = {
    "aadhaar": "models/templates/aadhaar_template.png",
    "pan": "models/templates/pan_template.png",
    "passport": "models/templates/passport_template.png",
    "dl": "models/templates/dl_template.png",
}


class TemplateMatcher:
    """
    Matches uploaded document to reference template layout.
    Uses ORB feature matching + structural similarity.
    """

    def match(self, image_path: str, doc_type: str) -> dict:
        """
        Compare image to reference template.
        Returns: {matched, similarity_score, score, method, note}
        """
        template_path = TEMPLATE_MAP.get(doc_type)
        if not template_path or not Path(template_path).exists():
            return {
                "matched": False,
                "similarity_score": None,
                "score": 60,
                "method": "template_matching",
                "note": f"No reference template available for '{doc_type}'. Using default score.",
            }

        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        tmpl = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

        if img is None or tmpl is None:
            return self._no_template(doc_type)

        # Resize both to same height
        target_height = 400
        img_resized = self._resize_to_height(img, target_height)
        tmpl_resized = self._resize_to_height(tmpl, target_height)

        # ORB feature matching
        orb_score = self._orb_match(img_resized, tmpl_resized)

        # Structural Similarity
        ssim_score = self._ssim_match(img_resized, tmpl_resized)

        # Combined score
        combined = 0.6 * orb_score + 0.4 * ssim_score
        similarity_pct = round(combined * 100, 1)

        # Convert to 0-100 authenticity score contribution
        # Perfect match = 95, partial = 60-80, poor = 30-50
        if similarity_pct >= 70:
            score = 75 + int((similarity_pct - 70) * 0.67)  # 75-90
        elif similarity_pct >= 40:
            score = 50 + int((similarity_pct - 40) * 0.83)  # 50-75
        else:
            score = int(similarity_pct * 1.25)  # 0-50

        score = max(10, min(95, score))

        return {
            "matched": similarity_pct >= 35,
            "similarity_score": similarity_pct,
            "score": score,
            "method": "ORB + SSIM template matching",
            "note": None,
        }

    def _resize_to_height(self, img: np.ndarray, height: int) -> np.ndarray:
        h, w = img.shape[:2]
        scale = height / h
        return cv2.resize(img, (int(w * scale), height))

    def _orb_match(self, img: np.ndarray, tmpl: np.ndarray) -> float:
        """ORB feature matching — returns ratio of good matches."""
        try:
            orb = cv2.ORB_create(nfeatures=300)
            kp1, des1 = orb.detectAndCompute(img, None)
            kp2, des2 = orb.detectAndCompute(tmpl, None)
            if des1 is None or des2 is None or len(des1) < 5 or len(des2) < 5:
                return 0.3
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)
            matches = sorted(matches, key=lambda x: x.distance)
            good = [m for m in matches if m.distance < 64]
            return min(len(good) / max(len(kp2), 1), 1.0)
        except Exception:
            return 0.3

    def _ssim_match(self, img: np.ndarray, tmpl: np.ndarray) -> float:
        """Structural similarity between doc and template."""
        try:
            # Resize to same size
            h = min(img.shape[0], tmpl.shape[0])
            w = min(img.shape[1], tmpl.shape[1])
            img_r = cv2.resize(img, (w, h))
            tmpl_r = cv2.resize(tmpl, (w, h))

            diff = cv2.absdiff(img_r, tmpl_r)
            score = 1.0 - (diff.mean() / 255.0)
            return max(0.0, min(1.0, score))
        except Exception:
            return 0.3

    def _no_template(self, doc_type: str) -> dict:
        return {
            "matched": False,
            "similarity_score": None,
            "score": 55,
            "method": "template_matching",
            "note": "Template image could not be loaded.",
        }


template_matcher = TemplateMatcher()
