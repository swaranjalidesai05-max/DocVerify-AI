import requests
import time
import os
import sys

BASE_URL = "http://127.0.0.1:8012"

def run_test(img_name, index):
    image_path = os.path.join(r"C:\Users\Swaranjali Desai\Downloads\Doc Verify AI\dataset\driving_license\images", img_name)
    
    print(f"\n--- Test {index}: {img_name} ---")
    start_time = time.time()
    
    with open(image_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/api/documents/upload", files={"file": f})
        
    doc_id = res.json()["document_id"]
    print(f"Uploaded. Document ID: {doc_id}")
    
    res = requests.post(f"{BASE_URL}/api/verification/start?doc_id={doc_id}")
    if res.status_code != 200:
        print("Failed to start:", res.text)
        return
        
    vid = res.json()["verification_id"]
    
    # Simulate UI polling
    while True:
        status_res = requests.get(f"{BASE_URL}/api/verification/{vid}")
        if status_res.status_code != 200:
            print("Error polling:", status_res.text)
            break
            
        data = status_res.json()
        status = data.get("status")
        stage = data.get("processing_stage", "...")
        verdict = data.get("verdict", "N/A")
        print(f"Poll UI -> [{status}] Verdict: {verdict} | Stage: {stage}")
        
        if status in ["completed", "failed"]:
            break
            
        time.sleep(1)
        
    duration = time.time() - start_time
    print(f"Total end-to-end time for test {index}: {duration:.2f}s")
    return duration

if __name__ == "__main__":
    images = os.listdir(r"C:\Users\Swaranjali Desai\Downloads\Doc Verify AI\dataset\driving_license\images")[:3]
    durations = []
    
    for i, img in enumerate(images, 1):
        if not img.endswith('.png'): continue
        d = run_test(img, i)
        durations.append(d)
        time.sleep(2) # brief pause between concurrent tests
        
    valid = [d for d in durations if d is not None]
    if valid:
        print(f"\nAverage Time: {sum(valid)/len(valid):.2f}s")
    
