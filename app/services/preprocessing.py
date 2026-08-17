"""
DocVerify AI - Image Preprocessing Pipeline
Phases: load → resize → grayscale → denoise → CLAHE → threshold → deskew → sharpen
"""
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Optional, Tuple
import io


class ImagePreprocessor:
    """Preprocessing pipeline for government document images."""

    TARGET_WIDTH = 1200  # Standard width for processing

    def preprocess(self, image_path: str) -> Tuple[np.ndarray, np.ndarray, dict]:
        """
        Full preprocessing pipeline.
        Returns: (preprocessed_bgr, original_bgr, stages_dict)
        """
        original = cv2.imread(image_path)
        if original is None:
            # Try with PIL
            pil_img = Image.open(image_path).convert("RGB")
            original = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        if original is None:
            raise ValueError(f"Could not load image: {image_path}")

        stages = {}
        stages["original"] = original.copy()

        # 1. Resize
        img = self._resize(original)
        stages["resized"] = img.copy()

        # 2. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        stages["grayscale"] = gray.copy()

        # 3. Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
        stages["denoised"] = denoised.copy()

        # 4. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        stages["enhanced"] = enhanced.copy()

        # 5. Deskew
        deskewed = self._deskew(enhanced)
        stages["deskewed"] = deskewed.copy()

        # 6. Sharpen
        sharpened = self._sharpen(deskewed)
        stages["sharpened"] = sharpened.copy()

        # Return preprocessed as BGR for downstream models
        preprocessed_bgr = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)

        return preprocessed_bgr, original, stages

    def _resize(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        if w > self.TARGET_WIDTH:
            scale = self.TARGET_WIDTH / w
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        elif w < 400:
            scale = 400 / w
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
        return img

    def _deskew(self, gray: np.ndarray) -> np.ndarray:
        """Detect and correct image skew."""
        try:
            coords = np.column_stack(np.where(gray > 0))
            if len(coords) < 10:
                return gray
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) < 0.5:
                return gray
            h, w = gray.shape
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return rotated
        except Exception:
            return gray

    def _sharpen(self, gray: np.ndarray) -> np.ndarray:
        """Apply unsharp masking for text enhancement."""
        blurred = cv2.GaussianBlur(gray, (0, 0), 3)
        sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
        return sharpened

    def preprocess_pil(self, pil_image: Image.Image) -> Tuple[np.ndarray, np.ndarray, dict]:
        """Preprocess from PIL image."""
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            pil_image.save(tmp.name)
            result = self.preprocess(tmp.name)
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
        return result


preprocessor = ImagePreprocessor()
