"""
Integration tests for Video2Doc MultiLang FastAPI Web Server.
"""
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_create_job_and_poll(client):
    # Create job with sample video and mock mode
    data = {
        "use_sample": "true",
        "source_lang": "ja",
        "target_langs": "vi,id",
        "use_mock": "true"
    }
    res = client.post("/api/jobs/create", data=data)
    assert res.status_code == 200
    job_id = res.json()["job_id"]
    assert job_id is not None

    # Check status endpoint
    status_res = client.get(f"/api/jobs/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ["pending", "processing", "completed"]


def test_web_ui_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Video2Doc MultiLang" in res.text
