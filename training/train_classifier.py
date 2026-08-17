import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from dataset_utils import get_dataloaders
import time

def train_model():
    print("Initializing training pipeline...")
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset')
    train_loader, val_loader, test_loader = get_dataloaders(dataset_path, batch_size=16)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Transfer learning with EfficientNet-B0
    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    
    # 5 classes: Aadhaar, PAN, Voter ID, Driving Licence, Passport
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, 5)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    num_epochs = 3 
    
    best_val_acc = 0.0
    
    model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'trained')
    os.makedirs(model_dir, exist_ok=True)
    save_path = os.path.join(model_dir, 'driving_license_classifier.pth')

    metrics_log = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

    print("Starting training (learning on Driving Licence data only)...")
    for epoch in range(num_epochs):
        since = time.time()
        
        # Training phase
        model.train()
        running_loss = 0.0
        running_corrects = 0

        for inputs, labels in train_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

        train_loss = running_loss / len(train_loader.dataset)
        train_acc = running_corrects.double() / len(train_loader.dataset)

        # Validation phase
        model.eval()
        val_running_loss = 0.0
        val_running_corrects = 0

        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                loss = criterion(outputs, labels)

                val_running_loss += loss.item() * inputs.size(0)
                val_running_corrects += torch.sum(preds == labels.data)

        val_loss = val_running_loss / len(val_loader.dataset)
        val_acc = val_running_corrects.double() / len(val_loader.dataset)
        
        metrics_log['train_loss'].append(train_loss)
        metrics_log['train_acc'].append(train_acc.item())
        metrics_log['val_loss'].append(val_loss)
        metrics_log['val_acc'].append(val_acc.item())

        time_elapsed = time.time() - since
        print(f"Epoch {epoch+1}/{num_epochs} - Time: {time_elapsed:.0f}s - Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} - Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), save_path)

    print(f"Training complete. Best val Acc: {best_val_acc:.4f}")
    print(f"Saved model to: {save_path}")

    # Generate small text file for metrics to be read by evaluate
    import json
    with open('training_metrics.json', 'w') as f:
        json.dump(metrics_log, f)

if __name__ == '__main__':
    train_model()
