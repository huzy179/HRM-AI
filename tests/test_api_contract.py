from __future__ import annotations

import importlib
import os
from pathlib import Path

from fastapi.testclient import TestClient


def _boot_app(tmp_path: Path) -> TestClient:
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}"

    # Reload DB session to pick up DATABASE_URL.
    import backend.db.session as session_mod

    importlib.reload(session_mod)

    from backend.db import models

    models.Base.metadata.create_all(bind=session_mod.engine)

    import backend.api.main as api_main

    importlib.reload(api_main)

    # Mock enqueue_job to avoid requiring Redis in unit tests.
    import backend.api.routes.campaigns as campaigns_routes
    import backend.api.routes.policy as policy_routes

    campaigns_routes.enqueue_job = lambda *_args, **_kwargs: "job_test_1"  # type: ignore[assignment]
    policy_routes.enqueue_job = lambda *_args, **_kwargs: "job_test_2"  # type: ignore[assignment]

    app = api_main.create_app()
    return TestClient(app)


def test_campaign_crud_and_uploads(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    client = _boot_app(tmp_path)

    r = client.post("/campaigns", json={"name": "camp_a"})
    assert r.status_code == 200
    camp_id = r.json()["id"]

    r = client.get("/campaigns")
    assert r.status_code == 200
    assert any(x["id"] == camp_id for x in r.json())

    r = client.post(
        f"/campaigns/{camp_id}/jd",
        files={"file": ("jd.txt", b"Hiring Python engineer", "text/plain")},
    )
    assert r.status_code == 200
    assert r.json()["job_id"] == "job_test_1"

    r = client.post(
        f"/campaigns/{camp_id}/cvs",
        files=[
            ("files", ("cv1.txt", b"Python FastAPI Docker", "text/plain")),
            ("files", ("cv2.txt", b"HR admin payroll", "text/plain")),
        ],
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["job_id"] == "job_test_1"
    assert len(body["candidate_ids"]) == 2

    cand_id = body["candidate_ids"][0]
    r = client.post(f"/campaigns/{camp_id}/candidates/{cand_id}/profile")
    assert r.status_code == 200
    assert r.json()["job_id"] == "job_test_1"


def test_policy_ingest_contract(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    client = _boot_app(tmp_path)

    r = client.post(
        "/policy/ingest",
        files=[
            ("files", ("policy1.txt", b"Quy dinh nghi phep: 12 ngay/nam", "text/plain")),
        ],
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["job_id"] == "job_test_2"
    assert body["doc_ids"]
