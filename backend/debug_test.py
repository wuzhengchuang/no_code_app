import sys
sys.path.insert(0, '/Users/wuchuang/Desktop/Git/no_code_app/backend/src')

import os
os.environ['DATABASE_URL'] = 'mysql+pymysql://root:password@localhost:3306/nocode_app_test?charset=utf8mb4'

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from src.main import app
from src.db.session import Base, get_db
from src.models.user import User
from src.core.security import get_password_hash

SQLALCHEMY_DATABASE_URL = 'mysql+pymysql://root:password@localhost:3306/nocode_app_test?charset=utf8mb4'
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = TestingSessionLocal()
email = 'test_debug@example.com'
user = User(
    email=email,
    password_hash=get_password_hash('password123'),
    nickname='Test User',
    status=1
)
db.add(user)
db.commit()
db.refresh(user)
db.close()

login_resp = client.post('/api/v1/auth/login', json={'email': email, 'password': 'password123'})
print('Login response:', login_resp.json())
token = login_resp.json()['data']['token']

create_resp = client.post('/api/v1/projects', json={'name': 'Test', 'target_platforms': ['h5']}, headers={'Authorization': f'Bearer {token}'})
print('Create project response:', create_resp.json())
project_id = create_resp.json()['data']['id']

update_resp = client.put(f'/api/v1/projects/{project_id}', json={'name': 'Updated'}, headers={'Authorization': f'Bearer {token}'})
print('Update project response:', update_resp.json())
print('Update project status:', update_resp.status_code)