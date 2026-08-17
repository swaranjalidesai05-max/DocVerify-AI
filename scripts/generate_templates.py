"""
DocVerify AI - Generate placeholder template images for document template matching.
These are synthetic reference layouts — replace with actual reference documents.
Run: python scripts/generate_templates.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed. Run: pip install pillow")
    sys.exit(1)

OUTPUT_DIR = "models/templates"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Standard document dimensions (in pixels at 150dpi equivalent)
CARD_W, CARD_H = 1012, 638    # ID card aspect ~1.59:1
PASSPORT_W, PASSPORT_H = 850, 1200  # Passport booklet page
A4_W, A4_H = 794, 1123       # A4 page

TEMPLATES = {
    "aadhaar_template": {
        "size": (CARD_W, CARD_H),
        "bg": (255, 247, 235),  # Warm cream
        "accent": (255, 127, 0),
        "title": "AADHAAR",
        "subtitle": "भारत सरकार | Government of India",
        "fields": ["Name:", "Date of Birth:", "Gender:", "Address:", "Aadhaar No:"],
        "has_photo": True,
        "has_qr": True,
    },
    "pan_template": {
        "size": (CARD_W, CARD_H),
        "bg": (240, 248, 255),  # Light blue
        "accent": (0, 112, 192),
        "title": "INCOME TAX DEPARTMENT",
        "subtitle": "Permanent Account Number Card",
        "fields": ["Name:", "Father's Name:", "Date of Birth:", "PAN No:"],
        "has_photo": True,
        "has_qr": False,
    },
    "passport_template": {
        "size": (PASSPORT_W, A4_H),
        "bg": (245, 240, 255),  # Light navy
        "accent": (30, 60, 120),
        "title": "REPUBLIC OF INDIA",
        "subtitle": "PASSPORT",
        "fields": ["Name:", "Passport No:", "Nationality:", "Date of Birth:", "Expiry:", "MRZ:"],
        "has_photo": True,
        "has_qr": False,
    },
    "dl_template": {
        "size": (CARD_W, CARD_H),
        "bg": (240, 255, 240),  # Light green
        "accent": (34, 139, 34),
        "title": "GOVERNMENT OF INDIA",
        "subtitle": "Driving Licence",
        "fields": ["Name:", "DL No:", "Date of Birth:", "Valid:", "Address:"],
        "has_photo": True,
        "has_qr": False,
    },
}

def draw_template(config, filename):
    w, h = config["size"]
    img = Image.new("RGB", (w, h), config["bg"])
    draw = ImageDraw.Draw(img)

    accent = config["accent"]
    
    # Header bar
    draw.rectangle([0, 0, w, 80], fill=accent)
    
    # Title text (simple, no custom font needed)
    draw.text((20, 20), config["title"], fill=(255,255,255))
    draw.text((20, 50), config["subtitle"], fill=(220,220,220))

    # Border
    draw.rectangle([4, 4, w-4, h-4], outline=accent, width=3)
    
    # Photo area
    if config.get("has_photo"):
        photo_x, photo_y = w - 200, 100
        draw.rectangle([photo_x, photo_y, photo_x+140, photo_y+170], outline=accent, width=2, fill=(220,220,220))
        draw.text((photo_x+30, photo_y+75), "PHOTO", fill=(150,150,150))

    # QR area
    if config.get("has_qr"):
        qr_x, qr_y = w - 200, 300
        draw.rectangle([qr_x, qr_y, qr_x+140, qr_y+140], outline=accent, width=2, fill=(200,200,200))
        # QR pattern simulation
        for i in range(0, 140, 20):
            for j in range(0, 140, 20):
                import random
                random.seed(i * 10 + j)
                if random.random() > 0.5:
                    draw.rectangle([qr_x+i, qr_y+j, qr_x+i+18, qr_y+j+18], fill=(80,80,80))

    # Field lines
    y = 100
    for field in config.get("fields", []):
        draw.text((30, y), field, fill=(80,80,80))
        draw.line([30, y+25, min(w-220, 500), y+25], fill=(150,150,150), width=1)
        y += 60

    # Bottom bar
    draw.rectangle([0, h-40, w, h], fill=accent)
    draw.text((20, h-28), "DEMO TEMPLATE — NOT A REAL DOCUMENT", fill=(255,255,200))

    outpath = os.path.join(OUTPUT_DIR, f"{filename}.png")
    img.save(outpath)
    print(f"  ✓ {outpath}")

print("Generating placeholder document templates...")
for name, cfg in TEMPLATES.items():
    draw_template(cfg, name)

print(f"\nTemplates saved to {OUTPUT_DIR}/")
print("Replace with real reference document images for production use.")
