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

    r = client.get(f"/campaigns/{camp_id}/settings")
    assert r.status_code == 200
    assert r.json()["campaign_id"] == camp_id

    r = client.put(
        f"/campaigns/{camp_id}/settings",
        json={"w_embed": 0.6, "required_skills": ["python", "docker"], "min_years_override": 2},
    )
    assert r.status_code == 200
    assert r.json()["w_embed"] == 0.6

    r = client.post(
        f"/campaigns/{camp_id}/jd",
        files={"file": ("jd.txt", b"Hiring Python engineer", "text/plain")},
    )
    assert r.status_code == 200
    assert r.json()["job_id"] == "job_test_1"
    assert r.headers.get("X-Request-Id")
    assert r.headers.get("X-Tenant-Id")

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


def test_ranking_returns_candidate_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    client = _boot_app(tmp_path)

    camp = client.post("/campaigns", json={"name": "Backend Developer - Tháng 7/2026"}).json()
    camp_id = camp["id"]
    upload = client.post(
        f"/campaigns/{camp_id}/cvs",
        files=[("files", ("cv1.txt", b"Python FastAPI Docker", "text/plain"))],
    ).json()
    cand_id = upload["candidate_ids"][0]

    from backend.db.session import SessionLocal
    from backend.db import models

    session = SessionLocal()
    try:
        cand = session.get(models.Candidate, cand_id)
        cand.parse_status = "OK"
        cand.parse_method = "markdown"
        cand.pipeline_status = "Shortlisted"
        session.add(
            models.ScreeningResult(
                campaign_id=camp_id,
                candidate_id=cand_id,
                tenant_id="default",
                score_embed=88.0,
                score_rules=70.0,
                score_total=82.6,
                evidence_json='["Python FastAPI Docker"]',
                rules_json='{"skills":["python"]}',
            )
        )
        session.commit()
    finally:
        session.close()

    r = client.get(f"/campaigns/{camp_id}/ranking")
    assert r.status_code == 200
    row = r.json()["results"][0]
    assert row["candidate_id"] == cand_id
    assert row["filename"] == "cv1.txt"
    assert row["pipeline_status"] == "Shortlisted"
    assert row["parse_status"] == "OK"


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

    # hygiene endpoints require confirm=true
    r = client.post("/policy/clear")
    assert r.status_code == 403
