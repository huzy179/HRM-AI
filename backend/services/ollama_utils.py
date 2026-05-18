from __future__ import annotations

import time
from typing import Any, Protocol


class _Invokable(Protocol):
    def invoke(self, input: Any, **kwargs: Any) -> Any: ...


def invoke_with_retry(
    llm: _Invokable,
    prompt: str,
    *,
    retries: int = 2,
    backoff_s: float = 1.0,
) -> Any:
    """
    Best-effort retry wrapper for transient Ollama/network errors.
    Retries are bounded and use linear backoff.
    """
    last_exc: Exception | None = None
    attempts = max(1, int(retries) + 1)
    for attempt in range(1, attempts + 1):
        try:
            return llm.invoke(prompt)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= attempts:
                raise
            sleep_s = max(0.0, float(backoff_s)) * attempt
            time.sleep(sleep_s)
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("INVOKE_FAILED_UNKNOWN")

