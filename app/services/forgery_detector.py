"""
DocVerify AI - Forgery Detection Engine
OpenCV-based forensic analysis. Detects potential manipulation.
NOT a guarantee of authenticity — produces risk indicators only.
"""
import cv2
import numpy as np
from typing import Optional
import math


class ForgeryDetector:
    """
    Baseline forensic analysis pipeline using OpenCV.
    Detects: ELA anomalies, edge inconsistencies, clone regions, texture anomalies.
    
    Interface designed for future deep-learning model replacement.
    """

    def analyze(self, image_path: str) -> dict:
        """
        Run full forensic analysis on a document image.
        Returns: {tampering_detected, confidence, suspicious_regions, anomalies, score}
        """
        img = cv2.imread(image_path)
        if img is None:
            return self._no_result("Could not load image")

        anomalies = []

        # Run each detection module
        ela_result = self._ela_analysis(image_path)
        if ela_result:
            anomalies.extend(ela_result)

        edge_result = self._edge_analysis(img)
        if edge_result:
            anomalies.extend(edge_result)

        noise_result = self._noise_analysis(img)
        if noise_result:
            anomalies.extend(noise_result)

        clone_result = self._clone_detection(img)
        if clone_result:
            anomalies.extend(clone_result)

        # Calculate overall tampering confidence
        if not anomalies:
            tampering_confidence = 0.05
            tampering_detected = False
        else:
            high_count = sum(1 for a in anomalies if a["severity"] == "HIGH")
            med_count = sum(1 for a in anomalies if a["severity"] == "MEDIUM")
            tampering_confidence = min(0.15 * high_count + 0.07 * med_count + 0.02 * len(anomalies), 0.95)
            tampering_detected = tampering_confidence > 0.25

        suspicious_regions = [a.get("region") for a in anomalies if a.get("region")]

        # Score: 100 = clean, 0 = heavily tampered
        forgery_score = max(0, 100 - int(tampering_confidence * 100))

        return {
            "tampering_detected": tampering_detected,
            "confidence": round(tampering_confidence, 3),
            "suspicious_regions": suspicious_regions,
            "anomalies": anomalies,
            "score": forgery_score,
        }

    def _ela_analysis(self, image_path: str) -> list:
        """Error Level Analysis — detect compression inconsistencies."""
        anomalies = []
        try:
            import tempfile, os
            from PIL import Image

            orig = Image.open(image_path).convert("RGB")
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name
                orig.save(tmp_path, "JPEG", quality=75)

            recompressed = Image.open(tmp_path)
            ela = np.abs(np.array(orig, dtype=np.float32) - np.array(recompressed, dtype=np.float32))
            os.unlink(tmp_path)

            ela_max = ela.max()
            ela_mean = ela.mean()

            # Detect high-ELA regions
            threshold = ela_mean + 2 * ela.std()
            ela_gray = ela.mean(axis=2)
            suspicious = (ela_gray > threshold).astype(np.uint8) * 255

            contours, _ = cv2.findContours(suspicious, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            large_contours = [c for c in contours if cv2.contourArea(c) > 500]

            if len(large_contours) >= 3:
                x, y, w, h = cv2.boundingRect(large_contours[0])
                anomalies.append({
                    "type": "ELA_INCONSISTENCY",
                    "severity": "MEDIUM" if ela_mean > 5 else "LOW",
                    "confidence": round(min(ela_mean / 20, 0.85), 2),
                    "explanation": (
                        f"Compression level analysis detected {len(large_contours)} regions with "
                        "inconsistent error levels. This may indicate localized edits or copy-paste operations."
                    ),
                    "region": [x, y, w, h] if large_contours else None,
                })
        except Exception:
            pass
        return anomalies

    def _edge_analysis(self, img: np.ndarray) -> list:
        """Detect unnatural edges that may indicate pasting or overwriting."""
        anomalies = []
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            h, w = gray.shape

            # Check regional edge density variance
            block_size = 64
            edge_densities = []
            for y in range(0, h - block_size, block_size):
                for x in range(0, w - block_size, block_size):
                    block = edges[y:y+block_size, x:x+block_size]
                    density = block.sum() / (block_size * block_size * 255)
                    edge_densities.append(density)

            if edge_densities:
                mean_d = np.mean(edge_densities)
                std_d = np.std(edge_densities)
                outliers = [d for d in edge_densities if abs(d - mean_d) > 2.5 * std_d]

                if len(outliers) > len(edge_densities) * 0.12:
                    anomalies.append({
                        "type": "EDGE_INCONSISTENCY",
                        "severity": "LOW",
                        "confidence": round(len(outliers) / max(len(edge_densities), 1), 2),
                        "explanation": (
                            "Abnormal edge density variation detected in some regions. "
                            "Font or image edges may differ from surrounding document content."
                        ),
                        "region": None,
                    })
        except Exception:
            pass
        return anomalies

    def _noise_analysis(self, img: np.ndarray) -> list:
        """Detect noise pattern inconsistencies across document regions."""
        anomalies = []
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            half = w // 2

            left = gray[:, :half].astype(float)
            right = gray[:, half:].astype(float)

            left_noise = np.std(left - cv2.GaussianBlur(left.astype(np.float32), (5, 5), 0))
            right_noise = np.std(right - cv2.GaussianBlur(right.astype(np.float32), (5, 5), 0))

            ratio = max(left_noise, right_noise) / max(min(left_noise, right_noise), 0.01)

            if ratio > 3.0:
                anomalies.append({
                    "type": "NOISE_INCONSISTENCY",
                    "severity": "MEDIUM" if ratio > 4.5 else "LOW",
                    "confidence": round(min((ratio - 3.0) / 5.0, 0.8), 2),
                    "explanation": (
                        f"Noise pattern is significantly different between document sections "
                        f"(ratio: {ratio:.1f}x). Different noise levels can indicate edited regions."
                    ),
                    "region": None,
                })
        except Exception:
            pass
        return anomalies

    def _clone_detection(self, img: np.ndarray) -> list:
        """Detect cloned/copy-pasted regions using ORB feature matching."""
        anomalies = []
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            orb = cv2.ORB_create(nfeatures=500)
            kp, des = orb.detectAndCompute(gray, None)

            if des is not None and len(kp) > 20:
                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                matches = bf.match(des, des)
                # Self-matches at different positions
                clone_matches = [
                    m for m in matches
                    if m.queryIdx != m.trainIdx
                    and cv2.norm(
                        np.array(kp[m.queryIdx].pt) - np.array(kp[m.trainIdx].pt)
                    ) > 30
                ]
                if len(clone_matches) > 15:
                    anomalies.append({
                        "type": "POSSIBLE_CLONE_REGION",
                        "severity": "LOW",
                        "confidence": round(min(len(clone_matches) / 100, 0.5), 2),
                        "explanation": (
                            f"Feature matching found {len(clone_matches)} potentially duplicated image regions. "
                            "This can appear in authentic documents with repeated patterns (seals, watermarks)."
                        ),
                        "region": None,
                    })
        except Exception:
            pass
        return anomalies

    def _no_result(self, reason: str) -> dict:
        return {
            "tampering_detected": False,
            "confidence": 0.0,
            "suspicious_regions": [],
            "anomalies": [{"type": "ANALYSIS_ERROR", "severity": "LOW", "confidence": 0, "explanation": reason, "region": None}],
            "score": 50,
        }

    def predict(self, image_path: str) -> dict:
        """Standard ML interface for future model replacement."""
        return self.analyze(image_path)


forgery_detector = ForgeryDetector()
