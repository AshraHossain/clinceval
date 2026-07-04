"""Retry, timeout, and circuit-breaker primitives for external dependencies
(Chroma, Anthropic API)."""
import functools
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout


def retry(times: int = 3, base_delay: float = 0.5, exceptions: tuple = (Exception,)):
    """Exponential backoff: base_delay * 2^attempt between tries."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(times):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < times - 1:
                        time.sleep(base_delay * (2 ** attempt))
            raise last_exc
        return wrapper
    return decorator


def call_with_timeout(fn, timeout_s: float, *args, **kwargs):
    """Run fn in a worker thread; raise TimeoutError if it exceeds timeout_s.
    (signal-based timeouts don't work off the main thread under uvicorn.)"""
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=timeout_s)
        except FutureTimeout:
            raise TimeoutError(f"{fn.__name__} exceeded {timeout_s}s")


class CircuitBreaker:
    """Fail fast after repeated failures instead of queueing doomed calls.

    closed -> (failures >= threshold) -> open -> (cooldown elapses) -> half-open trial.
    """

    def __init__(self, failure_threshold: int = 2, cooldown_s: float = 30.0):
        self.failure_threshold = failure_threshold
        self.cooldown_s = cooldown_s
        self.failures = 0
        self.opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.time() - self.opened_at >= self.cooldown_s:
            return False  # half-open: allow a trial call
        return True

    def call(self, fn, *args, **kwargs):
        if self.is_open:
            raise RuntimeError(f"circuit open: {self.failures} consecutive failures")
        try:
            result = fn(*args, **kwargs)
        except Exception:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.opened_at = time.time()
            raise
        self.failures = 0
        self.opened_at = None
        return result
