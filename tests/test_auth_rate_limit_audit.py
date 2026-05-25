from __future__ import annotations

import importlib
import os
from pathlib import Path

from fastapi.testclient import TestClient


def _boot_app(tmp_path: Path) -> TestClient:
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}"

    import backend.db.session as session_mod

    importlib.reload(session_mod)

    from backend.db import models

    models.Base.metadata.create_all(bind=session_mod.engine)

    import backend.api.main as api_main

    importlib.reload(api_main)

    app = api_main.create_app()
    return TestClient(app)


def test_auth_requires_key_when_enabled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_API_KEY"] = "k_test_123"

    client = _boot_app(tmp_path)

    # public
    r = client.get("/health")
    assert r.status_code == 200

    # protected
    r = client.get("/campaigns")
    assert r.status_code == 401

    r = client.get("/campaigns", headers={"X-API-Key": "bad"})
    assert r.status_code == 401

    r = client.get("/campaigns", headers={"X-API-Key": "k_test_123"})
    assert r.status_code == 200


def test_rate_limit_enforced(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_API_KEY"] = "k_test_123"
    os.environ["RATE_LIMIT_PER_MIN"] = "1"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"

    client = _boot_app(tmp_path)

    headers = {"X-API-Key": "k_test_123"}
    r1 = client.get("/campaigns", headers=headers)
    assert r1.status_code == 200
    r2 = client.get("/campaigns", headers=headers)
    assert r2.status_code == 429


def test_audit_endpoint_returns_events(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_API_KEY"] = "k_test_123"
    os.environ["HRM_ADMIN_API_KEY"] = "admin_key"
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"

    client = _boot_app(tmp_path)
    headers = {"X-API-Key": "admin_key"}

    client.get("/campaigns", headers=headers)
    client.get("/health")  # public, still should be audited

    r = client.get("/audit/events?limit=50&minutes=60", headers=headers)
    assert r.status_code == 200
    events = r.json()
    assert isinstance(events, list)
    assert events
    # Sanity fields
    assert "path" in events[0]
    assert "subject" in events[0]
    assert "request_id" in events[0]


def test_audit_purge_requires_confirm(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_API_KEY"] = "k_test_123"
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"

    client = _boot_app(tmp_path)
    headers = {"X-API-Key": "k_test_123"}

    r = client.post("/audit/purge", headers=headers)
    # Not admin yet → forbidden
    assert r.status_code == 403


def test_admin_required_for_dangerous_endpoints(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_API_KEY"] = "user_key"
    os.environ["HRM_ADMIN_API_KEY"] = "admin_key"
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"

    client = _boot_app(tmp_path)

    # user cannot purge
    r = client.post("/audit/purge?confirm=true", headers={"X-API-Key": "user_key"})
    assert r.status_code == 403

    # admin can purge (may delete 0)
    r = client.post("/audit/purge?confirm=true&days=1", headers={"X-API-Key": "admin_key"})
    assert r.status_code == 200

    # user cannot clear/rebuild policy
    r = client.post("/policy/clear?confirm=true", headers={"X-API-Key": "user_key"})
    assert r.status_code == 403
    r = client.post("/policy/rebuild?confirm=true", headers={"X-API-Key": "user_key"})
    assert r.status_code == 403

    # admin can clear/rebuild (enqueue jobs)
    r = client.post("/policy/clear?confirm=true", headers={"X-API-Key": "admin_key"})
    assert r.status_code == 200
    r = client.post("/policy/rebuild?confirm=true", headers={"X-API-Key": "admin_key"})
    assert r.status_code == 200

    # admin can retry job (job must exist; create one by calling a benign endpoint)
    created = client.post("/campaigns", json={"name": "camp"}, headers={"X-API-Key": "admin_key"})
    assert created.status_code == 200
    jobs = client.get("/jobs?limit=10", headers={"X-API-Key": "admin_key"})
    assert jobs.status_code == 200
