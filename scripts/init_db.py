"""
DocVerify AI - Database Initialization Script
Run: python scripts/init_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import create_tables, engine
from app.core.config import settings
import app.models.document
import app.models.verification

def main():
    print(f"Initializing database...")
    print(f"DATABASE_URL: {settings.DATABASE_URL[:30]}...")
    create_tables()
    print("✓ Tables created successfully")
    print(f"✓ Upload directory: {settings.upload_path}")
    print(f"✓ Report directory: {settings.report_path}")
    print("\nDatabase is ready. Run the application with:")
    print("  uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()
