from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient


def _boot_app(tmp_path: Path) -> tuple[TestClient, object]:
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}"

    import backend.db.session as session_mod

    importlib.reload(session_mod)

    from backend.db import models

    models.Base.metadata.create_all(bind=session_mod.engine)

    import backend.api.main as api_main

    importlib.reload(api_main)

    # Mock enqueue_job used by retry endpoint
    import backend.api.routes.jobs as jobs_routes

    jobs_routes.enqueue_job = lambda *_args, **_kwargs: "job_retry_1"  # type: ignore[assignment]

    return TestClient(api_main.create_app()), models


def test_retry_only_failed_done(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_ADMIN_API_KEY"] = "admin_key"
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"

    client, models = _boot_app(tmp_path)

    # create a RUNNING job
    from backend.db.session import SessionLocal

    s = SessionLocal()
    try:
        s.add(
            models.Job(
                id="job1",
                tenant_id="default",
                job_type="screen_campaign",
                payload_json=json.dumps({"campaign_id": 1}),
                status="RUNNING",
            )
        )
        s.commit()
    finally:
        s.close()

    r = client.post("/jobs/job1/retry?confirm=true", headers={"X-API-Key": "admin_key"})
    assert r.status_code == 409


def test_retry_blocks_unknown_job_type_without_force(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["HRM_ADMIN_API_KEY"] = "admin_key"
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    os.environ["RATE_LIMIT_AUTH_BONUS"] = "0"

    client, models = _boot_app(tmp_path)

    from backend.db.session import SessionLocal

    s = SessionLocal()
    try:
        s.add(
            models.Job(
                id="job2",
                tenant_id="default",
                job_type="unknown_type",
                payload_json="{}",
                status="FAILED",
            )
        )
        s.commit()
    finally:
        s.close()

    r = client.post("/jobs/job2/retry?confirm=true", headers={"X-API-Key": "admin_key"})
    assert r.status_code == 409

    r = client.post("/jobs/job2/retry?confirm=true&force=true", headers={"X-API-Key": "admin_key"})
    assert r.status_code == 200

