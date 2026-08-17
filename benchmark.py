import requests
import time
import os

BASE_URL = "http://127.0.0.1:8010"

def run_test():
    image_path = r"C:\Users\Swaranjali Desai\Downloads\Doc Verify AI\dataset\driving_license\images"
    image_file = os.listdir(image_path)[0]
    
    full_path = os.path.join(image_path, image_file)
    
    print(f"Uploading {image_file}...")
    start_time = time.time()
    
    with open(full_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/api/documents/upload", files={"file": f})
        
    if res.status_code != 200:
        print("Upload failed:", res.text)
        return
        
    doc_id = res.json()["document_id"]
    print(f"Uploaded successfully. Document ID: {doc_id}")
    
    res = requests.post(f"{BASE_URL}/api/verification/start?doc_id={doc_id}")
    if res.status_code != 200:
        print("Failed to start verification:", res.text)
        return
        
    vid = res.json()["verification_id"]
    
    print(f"Verification started. ID: {vid}. Polling for completion...")
    
    while True:
        v_res = requests.get(f"{BASE_URL}/api/verification/{vid}")
        if v_res.status_code == 200:
            status = v_res.json()["status"]
            if status in ["completed", "failed"]:
                print(f"Final status: {status}")
                break
        time.sleep(2)
        
    print(f"Entire client-side time: {time.time() - start_time:.2f}s")
    
if __name__ == "__main__":
    run_test()
