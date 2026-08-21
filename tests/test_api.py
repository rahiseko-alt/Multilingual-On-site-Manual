import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.app.main import app
from apps.api.app.db.base import Base
from apps.api.app.db.session import get_db
from apps.api.app.models.tenant import User, Tenant, TenantMember
from apps.api.app.models.project import Project
from apps.api.app.core.security import get_password_hash
from scripts.generate_sample_media import generate_sample_mp4

# Test DB Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create Tenant A & User A
    tenant_a = Tenant(id="tenant_a", name="Tenant A Corp")
    user_a = User(id="user_a", email="user_a@example.com", hashed_password=get_password_hash("password123"))
    member_a = TenantMember(tenant_id="tenant_a", user_id="user_a", role="owner")

    # Create Tenant B & User B
    tenant_b = Tenant(id="tenant_b", name="Tenant B Corp")
    user_b = User(id="user_b", email="user_b@example.com", hashed_password=get_password_hash("password123"))
    member_b = TenantMember(tenant_id="tenant_b", user_id="user_b", role="owner")

    db.add_all([tenant_a, user_a, member_a, tenant_b, user_b, member_b])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health_check():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_auth_and_tenant_isolation(tmp_path):
    # 1. Login User A
    res_a = client.post("/api/auth/login", json={"email": "user_a@example.com", "password": "password123"})
    assert res_a.status_code == 200
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Login User B
    res_b = client.post("/api/auth/login", json={"email": "user_b@example.com", "password": "password123"})
    assert res_b.status_code == 200
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates Project A
    res_proj = client.post("/api/projects", json={"title": "Project A Manual", "source_language": "ja", "target_languages": "vi,id"}, headers=headers_a)
    assert res_proj.status_code == 201
    proj_a_id = res_proj.json()["id"]

    # 4. User A can get Project A
    res_get_a = client.get(f"/api/projects/{proj_a_id}", headers=headers_a)
    assert res_get_a.status_code == 200
    assert res_get_a.json()["title"] == "Project A Manual"

    # 5. User B CANNOT get Project A (AC-012: Tenant Isolation)
    res_get_b = client.get(f"/api/projects/{proj_a_id}", headers=headers_b)
    assert res_get_b.status_code == 404

def test_project_workflow_and_async_processing(tmp_path):
    # Login
    res_login = client.post("/api/auth/login", json={"email": "user_a@example.com", "password": "password123"})
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Project
    proj_res = client.post("/api/projects", json={"title": "Assembly Line Manual", "source_language": "ja", "target_languages": "vi,id"}, headers=headers)
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # 2. Upload Video
    sample_mp4 = tmp_path / "sample.mp4"
    generate_sample_mp4(str(sample_mp4), duration=3)
    
    with open(sample_mp4, "rb") as f:
        upload_res = client.post(
            f"/api/projects/{project_id}/video",
            files={"file": ("sample.mp4", f, "video/mp4")},
            headers=headers
        )
    assert upload_res.status_code == 200
    assert upload_res.json()["duration"] > 0

    # 3. Trigger Processing (AC-013: HTTP 202 Accepted)
    process_res = client.post(f"/api/projects/{project_id}/process", headers=headers)
    assert process_res.status_code == 202
    job_id = process_res.json()["job_id"]
    assert process_res.json()["status"] == "queued"

    # 4. Check Job Status
    job_res = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert job_res.status_code == 200
    assert job_res.json()["project_id"] == project_id

    # 5. Add Glossary Term
    glossary_res = client.post(
        f"/api/projects/{project_id}/glossary",
        json={"source": "STARTボタン", "translations": {"vi": "nút START"}, "translate": True},
        headers=headers
    )
    assert glossary_res.status_code == 201
    assert glossary_res.json()["source"] == "STARTボタン"
