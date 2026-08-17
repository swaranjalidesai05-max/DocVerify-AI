"""End-to-end API test script focusing on stateless privacy constraints."""
import os, sys, json
sys.path.insert(0, '.')

from app.main import app
from starlette.testclient import TestClient
from app.core.state import active_documents

# Create an isolated client
client = TestClient(app, raise_server_exceptions=True, follow_redirects=False)

RESULTS = []

def check(label, cond, info=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label} {info}")
    RESULTS.append((label, cond))

# Vistor Dashboard Test
r = client.get('/dashboard')
check("Dashboard load", r.status_code == 200)

import io
from PIL import Image
img = Image.new('RGB', (300, 200), color=(200, 150, 100))
buf = io.BytesIO()
img.save(buf, format='JPEG')
buf.seek(0)

# Test 1 - Upload and check
r = client.post('/api/documents/upload', files={'file': ('visitor1_doc.jpg', buf, 'image/jpeg')})
check("Document upload", r.status_code == 200)
doc_id = r.json().get('document_id')

raw_path = active_documents.get(doc_id, {}).get('file_path')
check("Upload File Temporarily Created", os.path.exists(raw_path))

# verification
r = client.post(f'/api/verification/start?doc_id={doc_id}')
check("Start verification", r.status_code == 200)
ver_id = r.json().get('verification_id')

# Test 1 Verification: Confirm temporary file no longer exists
check("Temporary File Deleted After Processing", not os.path.exists(raw_path))
check("Temporary Document Memory State Cleared", doc_id not in active_documents)

# Verification Logic Assert
r = client.get(f'/api/verification/{ver_id}')
ver_data = r.json()
check("[Client 1] Classification Result Verification", ver_data.get('document_code') == 'AADHAAR', "Should detect AADHAAR in demo text")
check("No Raw text leaked into JSON response", 'raw_text' not in ver_data)
check("No PDF bytes leaked into JSON response", 'pdf_bytes' not in ver_data)

# Test 2 - No history
r = client.get(f'/api/history/')
check("History API 404", r.status_code == 404, "Endpoint should cease to exist")

# Test 4 - Report cleanup (Server does not retain report on disk)
r = client.get(f'/api/reports/{ver_id}')
check("Download PDF report", r.status_code == 200 and 'application/pdf' in r.headers.get('content-type',''))
check("PDF Bytes Sent Succesfully", len(r.content) > 1000)

check("No Database Leftovers", not os.path.exists("docverify.db"), "Should not serialize any DB footprints")


print("="*50)
fails = [l for l, c in RESULTS if not c]
if fails:
    print("FAILED TESTS:")
    for f in fails:
        print(f" - {f}")
    sys.exit(1)
else:
    print(f"PASSED: {len(RESULTS)}/{len(RESULTS)}")
    print("All tests passed! Privacy stateless architecture verified.")
    sys.exit(0)
