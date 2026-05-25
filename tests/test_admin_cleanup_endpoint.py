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

    # Mock enqueue_job to avoid Redis/RQ requirements
    import backend.api.routes.admin as admin_routes

    admin_routes.enqueue_job = lambda *_args, **_kwargs: "job_cleanup_1"  # type: ignore[assignment]

    app = api_main.create_app()
    return TestClient(app)


def test_admin_cleanup_requires_admin_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_API_KEY"] = "user_key"
    os.environ["HRM_ADMIN_API_KEY"] = "admin_key"
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"

    client = _boot_app(tmp_path)

    r = client.post("/admin/cleanup?confirm=true&dry_run=true", headers={"X-API-Key": "user_key"})
    assert r.status_code == 403

    r = client.post("/admin/cleanup?confirm=true&dry_run=true", headers={"X-API-Key": "admin_key"})
    assert r.status_code == 200
    assert r.json()["job_id"] == "job_cleanup_1"
