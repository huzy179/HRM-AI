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


def test_metrics_summary_basic(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_API_KEY"] = "k_test_123"
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"

    client = _boot_app(tmp_path)
    headers = {"X-API-Key": "k_test_123"}

    # generate a couple jobs in DB
    client.post("/campaigns", json={"name": "camp_a"}, headers=headers)
    client.get("/campaigns", headers=headers)

    r = client.get("/metrics/summary?minutes=60", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "jobs_total" in data
    assert "by_type" in data

