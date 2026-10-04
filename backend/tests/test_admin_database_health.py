import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import get_db, SessionLocal
from backend.app.models.user import User
from backend.app.api.deps import require_admin, get_current_user

def get_admin_override():
    user = User(
        id=1,
        name="Admin Test",
        email="admin@test.com",
        password_hash="hash",
        role="admin",
        is_active=True,
    )
    return user

@pytest.fixture
def client():
    app.dependency_overrides[require_admin] = get_admin_override
    app.dependency_overrides[get_current_user] = get_admin_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_database_health_live_count(client):
    res = client.get("/api/v1/admin/database/health")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "total_records" in data
    assert isinstance(data["total_records"], int)
    assert data["total_records"] > 0
    assert "tables" in data
    assert len(data["tables"]) > 0
    assert any(t["table_name"] == "transactions" and t["row_count"] > 0 for t in data["tables"])
    assert "SQLite" in data["engine"]

def test_database_download_endpoint(client):
    res = client.get("/api/v1/admin/database/download")
    assert res.status_code == 200, res.text
    assert "application/octet-stream" in res.headers["content-type"] or "application/x-sqlite3" in res.headers["content-type"]
    assert "content-disposition" in res.headers
    assert len(res.content) > 0
    # SQLite files begin with "SQLite format 3\x00"
    assert res.content.startswith(b"SQLite format 3\x00")
