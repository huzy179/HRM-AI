from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request


def _env_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default


RATE_LIMIT_PER_MIN = _env_int("RATE_LIMIT_PER_MIN", 120)
RATE_LIMIT_AUTH_BONUS = _env_int("RATE_LIMIT_AUTH_BONUS", 180)


@dataclass
class _MemBucket:
    window_start: int
    count: int


_MEM: dict[str, _MemBucket] = {}


def _client_ip(request: Request) -> str:
    xf = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if xf:
        return xf
    if request.client:
        return request.client.host
    return "unknown"


def _redis_client() -> Any | None:
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if not redis_url:
        return None
    try:
        from redis import Redis

        return Redis.from_url(redis_url)
    except Exception:
        return None


def enforce_rate_limit(request: Request, *, subject: str) -> None:
    """
    Fixed-window rate limiting (per minute).
    Uses Redis when available; otherwise falls back to in-memory process state.
    """
    limit = RATE_LIMIT_PER_MIN
    if subject.startswith("api_key:"):
        limit += max(0, RATE_LIMIT_AUTH_BONUS)

    now_s = int(time.time())
    window = now_s // 60
    ip = _client_ip(request)
    key = f"rl:{window}:{ip}:{subject}"

    r = _redis_client()
    if r is not None:
        try:
            count = int(r.incr(key))
            if count == 1:
                r.expire(key, 75)
        except Exception:
            r = None
        else:
            if count > limit:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            return

    bucket = _MEM.get(key)
    if bucket is None:
        _MEM[key] = _MemBucket(window_start=window, count=1)
        return
    if bucket.window_start != window:
        bucket.window_start = window
        bucket.count = 1
        return
    bucket.count += 1
    if bucket.count > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

