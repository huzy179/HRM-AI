from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_KEY = (os.environ.get("API_KEY") or "").strip()


def _headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h: Dict[str, str] = {}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    if extra:
        h.update(extra)
    return h


def get(path: str, *, timeout: int = 30) -> requests.Response:
    return requests.get(f"{API_BASE_URL}{path}", headers=_headers(), timeout=timeout)


def post(path: str, *, json: Any = None, files: Any = None, timeout: int = 60) -> requests.Response:
    return requests.post(f"{API_BASE_URL}{path}", json=json, files=files, headers=_headers(), timeout=timeout)


def put(path: str, *, json: Any = None, timeout: int = 60) -> requests.Response:
    return requests.put(f"{API_BASE_URL}{path}", json=json, headers=_headers(), timeout=timeout)

