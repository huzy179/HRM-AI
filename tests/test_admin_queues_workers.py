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

    return TestClient(api_main.create_app())


def test_admin_queues_requires_redis_url(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_ADMIN_API_KEY"] = "admin_key"
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"
    os.environ.pop("REDIS_URL", None)

    client = _boot_app(tmp_path)
    r = client.get("/admin/queues", headers={"X-API-Key": "admin_key"})
    assert r.status_code == 503


def test_admin_workers_requires_redis_url(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_ADMIN_API_KEY"] = "admin_key"
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"
    os.environ.pop("REDIS_URL", None)

    client = _boot_app(tmp_path)
    r = client.get("/admin/workers", headers={"X-API-Key": "admin_key"})
    assert r.status_code == 503

