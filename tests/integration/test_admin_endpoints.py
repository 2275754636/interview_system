from __future__ import annotations

from fastapi.testclient import TestClient

from interview_system.api.main import create_app
from interview_system.config.settings import Settings


def test_admin_endpoints_disabled_by_default():
    app = create_app(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            log_level="INFO",
            allowed_origins=[],
        )
    )

    with TestClient(app) as client:
        r = client.get("/api/admin/overview")
        assert r.status_code == 404
        payload = r.json()
        assert payload["error"]["code"] == "ADMIN_DISABLED"


def test_admin_overview_search_and_export():
    token = "secret-token"
    app = create_app(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            log_level="INFO",
            allowed_origins=[],
            admin_token=token,
        )
    )

    with TestClient(app) as client:
        unauthorized = client.get("/api/admin/overview")
        assert unauthorized.status_code == 401
        assert unauthorized.json()["error"]["code"] == "ADMIN_UNAUTHORIZED"

        start = client.post("/api/session/start", json={"user_name": "tester"})
        assert start.status_code == 200
        session_id = start.json()["session"]["id"]

        send = client.post(f"/api/session/{session_id}/message", json={"text": "我认为教学应该以学生为中心"})
        assert send.status_code == 200

        headers = {"X-Admin-Token": token}

        overview = client.get("/api/admin/overview?bucket=day", headers=headers)
        assert overview.status_code == 200
        data = overview.json()
        assert "summary" in data
        assert "time_series" in data

        search = client.get(
            "/api/admin/search?keyword=%E5%AD%A6%E7%94%9F&limit=10",
            headers=headers,
        )
        assert search.status_code == 200
        search_payload = search.json()
        assert search_payload["total"] >= 1

        export_csv = client.get(
            "/api/admin/export?format=csv&scope=conversations&limit=100",
            headers=headers,
        )
        assert export_csv.status_code == 200
        assert b"session_id" in export_csv.content

        export_json = client.get(
            "/api/admin/export?format=json&scope=conversations&limit=100",
            headers=headers,
        )
        assert export_json.status_code == 200
        assert export_json.headers.get("content-type", "").startswith("application/json")
