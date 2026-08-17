import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms
from PIL import Image

class DocumentDataset(Dataset):
    def __init__(self, root_dir, csv_file, transform=None, label_idx=3):
        # label_idx 3 corresponds to Driving Licence in a proposed 5-class system:
        # [0: Aadhaar, 1: PAN, 2: Voter ID, 3: Driving Licence, 4: Passport]
        self.root_dir = root_dir
        self.df = pd.read_csv(os.path.join(os.path.dirname(root_dir), csv_file))
        # Keep only valid images
        self.image_files = [f for f in os.listdir(root_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        # Filter dataframe to only images that exist
        self.df = self.df[self.df['filename'].isin(self.image_files)].reset_index(drop=True)
        self.transform = transform
        self.label_idx = label_idx
        
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        img_name = self.df.iloc[idx]['filename']
        img_path = os.path.join(self.root_dir, img_name)
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
            
        return image, self.label_idx

def get_dataloaders(dataset_path, batch_size=32):
    # Base configuration
    images_dir = os.path.join(dataset_path, 'driving_license', 'images')
    csv_file = 'labels.csv'
    
    # 2.5 DATA AUGMENTATION (Training only)
    # - small rotation
    # - brightness variation
    # - contrast variation
    # - mild blur
    # - mild JPEG compression (simulate it via lower quality resize/interpolation or noise)
    # - mild perspective transformation
    # - mild noise
    # - slight scaling
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomAffine(degrees=5, translate=(0.02, 0.02), scale=(0.95, 1.05), shear=2),
        transforms.RandomPerspective(distortion_scale=0.1, p=0.5),
        transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
        transforms.GaussianBlur(kernel_size=(3, 3), sigma=(0.1, 1.0)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Validation/Test only gets resize and normalize (no augmentation)
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # 2.4 TRAIN/VALIDATION/TEST SPLIT
    # Load dataset with NO transform first to get split indices, then apply transforms wrapper
    full_dataset = DocumentDataset(images_dir, csv_file, transform=None)
    total_size = len(full_dataset)
    
    train_size = int(0.7 * total_size)
    val_size = int(0.15 * total_size)
    test_size = total_size - train_size - val_size
    
    # Split the dataset
    train_dataset, val_dataset, test_dataset = random_split(
        full_dataset, [train_size, val_size, test_size],
        generator=torch.Generator().manual_seed(42)
    )
    
    # Wrapper class to apply transforms to subsets
    class DatasetWrapper(Dataset):
        def __init__(self, subset, transform):
            self.subset = subset
            self.transform = transform
        def __len__(self):
            return len(self.subset)
        def __getitem__(self, idx):
            img, label = self.subset[idx]
            if self.transform:
                img = self.transform(img)
            return img, label

    train_wrapper = DatasetWrapper(train_dataset, train_transform)
    val_wrapper = DatasetWrapper(val_dataset, eval_transform)
    test_wrapper = DatasetWrapper(test_dataset, eval_transform)
    
    train_loader = DataLoader(train_wrapper, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_wrapper, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_wrapper, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader, test_loader
