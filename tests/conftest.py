from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _reset_security_env() -> None:
    """
    Ensure security/rate-limit env vars don't leak across tests.
    Individual tests can set them via monkeypatch.setenv.
    """
    for k in [
        "HRM_API_KEY",
        "HRM_API_KEYS",
        "HRM_ADMIN_API_KEY",
        "HRM_ADMIN_API_KEYS",
        "RATE_LIMIT_PER_MIN",
        "RATE_LIMIT_AUTH_BONUS",
    ]:
        os.environ.pop(k, None)

    # Clear in-memory rate limit buckets between tests
    try:
        from backend.api import rate_limit

        rate_limit.reset_memory_state()
    except Exception:
        pass
