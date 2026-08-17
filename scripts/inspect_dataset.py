import pandas as pd
import os
import json
from PIL import Image

def inspect_dataset():
    image_dir = r'C:\Users\Swaranjali Desai\Downloads\Doc Verify AI\dataset\driving_license\images'
    csv_path = r'C:\Users\Swaranjali Desai\Downloads\Doc Verify AI\dataset\driving_license\labels.csv'

    df = pd.read_csv(csv_path)
    
    files = os.listdir(image_dir)
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    csv_filenames = set(df['filename'].tolist()) if 'filename' in df.columns else set(df.iloc[:, 0].tolist())
    folder_filenames = set(image_files)

    missing_in_csv = folder_filenames - csv_filenames
    missing_in_folder = csv_filenames - folder_filenames
    
    # Check duplicates in CSV
    duplicates_csv = len(df) - len(df['filename'].unique()) if 'filename' in df.columns else 0

    valid_images = 0
    corrupted_images = 0
    dimensions = {}
    formats = {}

    for img_file in folder_filenames:
        try:
            with Image.open(os.path.join(image_dir, img_file)) as img:
                img.verify()
                valid_images += 1
                size_str = f"{img.size[0]}x{img.size[1]}"
                dimensions[size_str] = dimensions.get(size_str, 0) + 1
                formats[img.format] = formats.get(img.format, 0) + 1
        except Exception:
            corrupted_images += 1

    report = {
        'total_images_in_folder': len(image_files),
        'total_rows_in_csv': len(df),
        'missing_in_csv_count': len(missing_in_csv),
        'missing_in_folder_count': len(missing_in_folder),
        'duplicates_in_csv': duplicates_csv,
        'valid_images': valid_images,
        'corrupted_images': corrupted_images,
        'image_dimensions': dimensions,
        'image_formats': formats,
        'csv_columns': df.columns.tolist()
    }
    
    with open('inspect_report.json', 'w') as f:
        json.dump(report, f, indent=4)

if __name__ == '__main__':
    inspect_dataset()
