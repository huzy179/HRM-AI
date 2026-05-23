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
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"

    client = _boot_app(tmp_path)
    headers = {"X-API-Key": "k_test_123"}

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
