"""
DocVerify AI - Document Classifier
Hybrid approach: Uses PyTorch EfficientNet-B0 model if available and highly confident,
otherwise yields to OCR keyword scoring + layout heuristics.
"""
from typing import Optional
import re
import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

from app.config.document_types import DOCUMENT_CONFIGS
from app.core.config import settings

class DocumentClassifier:
    """
    Classifies document type using the trained ML model, falling back to OCR text / visual heuristics.
    """
    def __init__(self):
        self.device = torch.device("cpu")
        self.model = None
        self.transform = None
        self.class_names = {0: "Aadhaar", 1: "PAN", 2: "Voter ID", 3: "Driving Licence", 4: "Passport"}
        self.class_codes = {0: "AADHAAR", 1: "PAN", 2: "VOTER_ID", 3: "DRIVING_LICENSE", 4: "PASSPORT"}
        
    def _load_model(self):
        try:
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            model_path = os.path.join(root_dir, 'training', 'models', 'driving_license_classifier.pth')
            if os.path.exists(model_path):
                self.model = models.efficientnet_b0(weights=None)
                num_ftrs = self.model.classifier[1].in_features
                self.model.classifier[1] = nn.Linear(num_ftrs, 5)
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                self.model.eval()
                
                self.transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                ])
                print("[ML] Successfully loaded Document Classifier model.")
        except Exception as e:
            self.model = None
            print(f"Could not load ML model: {e}")

    def classify(self, raw_text: str, image_path: Optional[str] = None) -> dict:
        """
        Attempts ML inference first if an image is provided.
        Falls back to keyword search if confidence is too low or image is missing.
        """
        if self.model is None and image_path:
            self._load_model()

        # --- 1. ML CLASSIFICATION ---
        if self.model and image_path and os.path.exists(image_path):
            try:
                image = Image.open(image_path).convert('RGB')
                tensor = self.transform(image).unsqueeze(0).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(tensor)
                    probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
                    confidence, predicted = torch.max(probabilities, 0)
                    
                    idx = predicted.item()
                    conf_pct = float(confidence.item()) * 100.0
                    
                    if conf_pct >= 60.0:  # Threshold to trust ML model
                        status = "SUPPORTED" if conf_pct >= 75.0 else "UNCERTAIN"
                        # Ensure the code maps correctly if index is 3 (Driving Licence)
                        return {
                            "document_type": self.class_names[idx],
                            "document_code": self.class_codes[idx],
                            "confidence": round(conf_pct, 1),
                            "classification_method": "EfficientNet-B0 ML Model",
                            "status": status,
                        }
            except Exception as e:
                print(f"[ML] classification inference failed: {e}")
                
        # --- 2. FALLBACK OCR CLASSIFICATION ---
        if not raw_text or raw_text.strip() == "":
            return self._unknown(0.0)

        text_lower = raw_text.lower()
        scores = {}

        for doc_code, config in DOCUMENT_CONFIGS.items():
            score = 0.0
            total_keywords = len(config["keywords"])
            matched_keywords = sum(
                1 for kw in config["keywords"] if kw.lower() in text_lower
            )
            score += (matched_keywords / max(total_keywords, 1)) * 50.0

            for pattern in config.get("strong_patterns", []):
                if re.search(pattern, raw_text, re.IGNORECASE):
                    score += 45.0
                    break

            scores[doc_code] = min(score, 100.0)

        if not scores or max(scores.values()) < settings.CLASSIFICATION_CONFIDENCE_UNCERTAIN:
            max_c = max(scores.values()) if scores else 0.0
            return self._unknown(max_c)

        best_code = max(scores, key=scores.get)
        best_score = scores[best_code]
        confidence = best_score
        
        status = "SUPPORTED"
        if confidence < settings.CLASSIFICATION_CONFIDENCE_SUPPORTED:
            status = "UNCERTAIN"
        
        if confidence < settings.CLASSIFICATION_CONFIDENCE_UNCERTAIN:
            return self._unknown(confidence)

        display_name = DOCUMENT_CONFIGS[best_code]["display_name"] if best_code in DOCUMENT_CONFIGS else "Unknown"

        return {
            "document_type": display_name,
            "document_code": best_code,
            "confidence": round(confidence, 1),
            "classification_method": "Hybrid baseline classifier (OCR)",
            "status": status,
        }

    def _unknown(self, conf: float = 0.0) -> dict:
        return {
            "document_type": "Unknown / Unsupported",
            "document_code": "UNKNOWN",
            "confidence": round(conf, 1),
            "classification_method": "Hybrid baseline classifier",
            "status": "UNSUPPORTED",
        }

    def predict(self, image_path: str, raw_text: str = "") -> dict:
        """Standard ML interface for future model replacement."""
        return self.classify(raw_text, image_path)

document_classifier = DocumentClassifier()
