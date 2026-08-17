import os
import torch
import torch.nn as nn
from torchvision import models
from dataset_utils import get_dataloaders
import json

def evaluate_model():
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset')
    _, _, test_loader = get_dataloaders(dataset_path, batch_size=16)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = models.efficientnet_b0(weights=None)
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, 5)
    
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'trained', 'driving_license_classifier.pth')
    if not os.path.exists(model_path):
        print("Model not found. Please run train_classifier.py first.")
        return
        
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model = model.to(device)
    model.eval()

    all_preds = []
    all_labels = []

    print("Running evaluation on test set...")
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # Manual metrics
    correct = sum(1 for p, l in zip(all_preds, all_labels) if p == l)
    total = len(all_labels)
    acc = correct / total if total > 0 else 0
    
    # We only care about class 3 today since it's the only one in the dataset
    true_positives = sum(1 for p, l in zip(all_preds, all_labels) if p == 3 and l == 3)
    predicted_positives = sum(1 for p in all_preds if p == 3)
    actual_positives = sum(1 for l in all_labels if l == 3)

    prec = true_positives / predicted_positives if predicted_positives > 0 else 0
    rec = true_positives / actual_positives if actual_positives > 0 else 0
    f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0

    print("\n--- MODEL METRICS ---")
    
    try:
        with open('training_metrics.json', 'r') as f:
            t_metrics = json.load(f)
            print(f"Final Train Accuracy: {t_metrics['train_acc'][-1]:.4f}")
            print(f"Final Val Accuracy: {t_metrics['val_acc'][-1]:.4f}")
            print(f"Final Train Loss: {t_metrics['train_loss'][-1]:.4f}")
            print(f"Final Val Loss: {t_metrics['val_loss'][-1]:.4f}")
    except Exception:
        pass

    print(f"\nTest Accuracy: {acc:.4f}")
    print(f"Precision (Driving Licence): {prec:.4f}")
    print(f"Recall (Driving Licence): {rec:.4f}")
    print(f"F1-Score (Driving Licence): {f1:.4f}")
    
    # Print Confusion matrix for 5 classes
    print("\nConfusion Matrix (Rows: True, Cols: Pred):")
    print("[Aadhaar, PAN, Voter ID, Driving Licence, Passport]")
    cm = [[0]*5 for _ in range(5)]
    for p, l in zip(all_preds, all_labels):
        if l < 5 and p < 5:
            cm[l][p] += 1
            
    for row in cm:
        print(row)

    print("\nNote: Only Driving Licence (index 3) is present in the current dataset.")

if __name__ == '__main__':
    evaluate_model()
