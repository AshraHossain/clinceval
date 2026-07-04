"""Structured JSON logging with request correlation.

Every API request gets a request_id (X-Request-ID header, generated if absent),
one JSON log line with latency and status, and PII-redacted query text.
"""
import json
import logging
import sys
import time
import uuid

from app.security import redact_pii


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("request_id", "latency_ms", "status", "path", "query_preview", "api_key"):
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def get_logger(name: str = "clinceval") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def install_request_logging(app):
    """FastAPI middleware: request_id propagation + one structured line per request."""
    logger = get_logger()

    @app.middleware("http")
    async def log_requests(request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        start = time.time()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": round((time.time() - start) * 1000, 1),
            },
        )
        return response

    return app


def log_query(logger: logging.Logger, query: str, request_id: str | None = None) -> None:
    """Audit-log a query with PII redacted; never log the raw text."""
    logger.info(
        "recommend_query",
        extra={
            "request_id": request_id,
            "query_preview": redact_pii(query)[:200],
        },
    )
