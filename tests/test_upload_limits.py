from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _boot_app(tmp_path: Path) -> TestClient:
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}"

    import backend.db.session as session_mod

    importlib.reload(session_mod)

    from backend.db import models

    models.Base.metadata.create_all(bind=session_mod.engine)

    import backend.api.main as api_main

    importlib.reload(api_main)

    # Mock queue
    import backend.api.routes.campaigns as campaigns_routes

    campaigns_routes.enqueue_job = lambda *_args, **_kwargs: "job_test_1"  # type: ignore[assignment]

    app = api_main.create_app()
    return TestClient(app)


def test_upload_rejects_large_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["MAX_UPLOAD_BYTES"] = "10"

    import backend.api.upload_limits as limits

    importlib.reload(limits)

    client = _boot_app(tmp_path)
    r = client.post("/campaigns", json={"name": "camp_a"})
    camp_id = r.json()["id"]

    payload = b"x" * 20
    r = client.post(
        f"/campaigns/{camp_id}/jd",
        files={"file": ("jd.txt", payload, "text/plain")},
    )
    assert r.status_code == 413


def test_upload_rejects_too_many_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    os.environ["MAX_UPLOAD_FILES"] = "1"

    import backend.api.upload_limits as limits

    importlib.reload(limits)

    client = _boot_app(tmp_path)
    r = client.post("/campaigns", json={"name": "camp_a"})
    camp_id = r.json()["id"]

    r = client.post(
        f"/campaigns/{camp_id}/cvs",
        files=[
            ("files", ("cv1.txt", b"a", "text/plain")),
            ("files", ("cv2.txt", b"b", "text/plain")),
        ],
    )
    assert r.status_code == 413

