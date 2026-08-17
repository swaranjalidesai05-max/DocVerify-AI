"""
DocVerify AI - Optional Face Verification Service
Compares selfie against document photograph using DeepFace.
Gracefully disabled when ENABLE_FACE_VERIFICATION=false or DeepFace unavailable.
"""
from app.core.config import settings


class FaceVerifier:
    """
    Optional face comparison service.
    Uses DeepFace if available and enabled. Returns NOT_AVAILABLE when disabled.
    """

    def verify(self, document_image_path: str, selfie_image_path: str) -> dict:
        """
        Compare face in document against selfie.
        Returns: {face_detected, similarity, match, confidence, note}
        """
        if not settings.ENABLE_FACE_VERIFICATION:
            return self._not_available("Face verification is disabled in configuration")

        try:
            import cv2
            # Attempt to extract face from document
            doc_face = self._extract_face(document_image_path)
            if doc_face is None:
                return self._error("No face detected in document image")

            selfie_face = self._extract_face(selfie_image_path)
            if selfie_face is None:
                return self._error("No face detected in selfie image")

            # Try DeepFace
            return self._deepface_compare(document_image_path, selfie_image_path)

        except Exception as e:
            return self._error(f"Face verification failed: {str(e)}")

    def _extract_face(self, image_path: str):
        """Detect face in image using OpenCV Haar cascade."""
        try:
            import cv2
            img = cv2.imread(image_path)
            if img is None:
                return None
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
            return faces if len(faces) > 0 else None
        except Exception:
            return None

    def _deepface_compare(self, img1: str, img2: str) -> dict:
        """Use DeepFace for verification."""
        try:
            from deepface import DeepFace
            result = DeepFace.verify(
                img1_path=img1,
                img2_path=img2,
                model_name="VGG-Face",
                enforce_detection=False,
            )
            similarity = (1 - result.get("distance", 0.5)) * 100
            return {
                "face_detected": True,
                "similarity": round(similarity, 1),
                "match": result.get("verified", False),
                "confidence": round(1 - result.get("threshold_to_verify", 0.4), 2),
                "note": None,
            }
        except ImportError:
            return self._not_available("DeepFace not installed")
        except Exception as e:
            return self._error(str(e))

    def _not_available(self, reason: str) -> dict:
        return {
            "face_detected": False,
            "similarity": None,
            "match": None,
            "confidence": None,
            "note": reason,
            "not_available": True,
        }

    def _error(self, reason: str) -> dict:
        return {
            "face_detected": False,
            "similarity": None,
            "match": None,
            "confidence": None,
            "note": reason,
            "not_available": False,
        }


face_verifier = FaceVerifier()
