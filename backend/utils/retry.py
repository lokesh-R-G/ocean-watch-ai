from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def run_with_retries(
    operation: Callable[[], T],
    retries: int,
    backoff_seconds: float,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    last_error: Exception | None = None

    attempts = max(1, retries)
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except retry_exceptions as exc:  # pragma: no cover - simple retry helper
            last_error = exc
            if attempt == attempts:
                break
            sleep_seconds = backoff_seconds * attempt
            time.sleep(sleep_seconds)

    if last_error is not None:
        raise last_error

    raise RuntimeError("Retry operation failed without an exception")
