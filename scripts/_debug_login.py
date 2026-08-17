"""Debug script to check version compatibility and identify the exact 500 error."""
import os, sys, traceback
sys.path.insert(0, '.')
os.environ['DATABASE_URL'] = 'sqlite:///./docverify.db'

import fastapi, starlette, jinja2, sqlalchemy
print(f'FastAPI: {fastapi.__version__}')
print(f'Starlette: {starlette.__version__}')
print(f'Jinja2: {jinja2.__version__}')
print(f'SQLAlchemy: {sqlalchemy.__version__}')

from app.core.database import create_tables
create_tables()
from app.main import app
from starlette.testclient import TestClient

try:
    # Test with raise_server_exceptions=True to get exact traceback
    client = TestClient(app, raise_server_exceptions=True)
    r = client.get('/login', follow_redirects=False)
    print(f'Login status: {r.status_code}')
    if r.status_code in (301, 302, 307, 308):
        print(f'Redirect to: {r.headers.get("location")}')
    elif r.status_code == 200:
        print('Login page OK')
    else:
        print('Error body:', r.text[:500])
except Exception as e:
    print(f'Exception type: {type(e).__name__}')
    traceback.print_exc()
