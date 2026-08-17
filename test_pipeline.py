import os
import uuid
import sys
import time
import shutil
from app.services.verification_pipeline import verification_pipeline
from app.core.state import active_documents, active_verifications
from app.utils.file_utils import delete_file_safe

def run_isolated():
    image_path = r"C:\Users\Swaranjali Desai\Downloads\Doc Verify AI\dataset\driving_license\images"
    image_list = [f for f in os.listdir(image_path) if f.endswith('.png')]
    first_image = os.path.join(image_path, image_list[0])
    
    # Create temp copy so pipeline doesn't delete the original
    upload_target = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', f"temp_bench_{uuid.uuid4()}.png")
    os.makedirs(os.path.dirname(upload_target), exist_ok=True)
    shutil.copy(first_image, upload_target)
    
    # Mock upload
    doc_id = str(uuid.uuid4())
    active_documents[doc_id] = {
        "id": doc_id,
        "original_filename": image_list[0],
        "file_path": upload_target,
        "file_size": os.path.getsize(upload_target),
    }
    
    vid = str(uuid.uuid4())
    active_verifications[vid] = {
        "verification_id": vid,
        "document_id": doc_id,
    }
    
    print(f"Starting test for document {upload_target}")
    
    try:
        verification_pipeline.verify_stateless(doc_id, vid)
        print("Success! Final Verdict:", active_verifications[vid].get("verdict"))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    run_isolated()
