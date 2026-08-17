# ML Training Pipeline

This folder contains the complete machine learning training pipeline for document classification, architected to classify up to 5 document types (`Aadhaar`, `PAN`, `Voter ID`, `Driving Licence`, `Passport`), but currently trained exclusively with the **Driving Licence** dataset.

## Scripts:

- `dataset_utils.py`: Contains standard datasets/dataloaders creation handling (train/val/test splits). Incorporates data augmentation to the train subsets (affine, perspective, color jittering, minimal blurs, and scaling).
- `train_classifier.py`: Trains the EfficientNet-B0 model via PyTorch.
- `evaluate.py`: Generates actual validation test metrics: Accuracy, Precision, Recall, Confusion Matrix.

## Workflow:
1. Ensure the dataset exists properly structured inside `/dataset/driving_license/...`.
2. Run `python training/train_classifier.py`.
3. Run `python training/evaluate.py`.
4. Outputs will be placed safely inside `models/trained/`.
