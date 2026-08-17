"""DocVerify AI - Image Utilities"""
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Optional


def pil_to_cv(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to OpenCV BGR array."""
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def cv_to_pil(image: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR array to PIL Image."""
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def load_image_cv(path: str) -> Optional[np.ndarray]:
    """Load image with OpenCV from file path."""
    img = cv2.imread(path)
    return img


def load_image_pil(path: str) -> Optional[Image.Image]:
    """Load image with PIL from file path."""
    try:
        return Image.open(path).convert("RGB")
    except Exception:
        return None


def draw_bounding_boxes(image: np.ndarray, regions: list, color=(0, 0, 255), thickness=2) -> np.ndarray:
    """Draw bounding boxes on image for anomaly visualization."""
    result = image.copy()
    for region in regions:
        if region and len(region) == 4:
            x, y, w, h = int(region[0]), int(region[1]), int(region[2]), int(region[3])
            cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
    return result


def resize_for_display(image: np.ndarray, max_width: int = 800) -> np.ndarray:
    """Resize image to max_width preserving aspect ratio."""
    h, w = image.shape[:2]
    if w <= max_width:
        return image
    scale = max_width / w
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h))


def encode_image_base64(image: np.ndarray) -> str:
    """Encode OpenCV image to base64 PNG for embedding in HTML."""
    import base64
    _, buffer = cv2.imencode(".png", image)
    return base64.b64encode(buffer).decode("utf-8")
