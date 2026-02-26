"""Package de gestion centralisée des erreurs du scan."""

from app.errors.fetch_errors import (
    FetchResult,
    build_sse_error_payload,
    build_timeout_global_error_payload,
    build_unexpected_error_payload,
    build_validation_error_payload,
    classify_fetch_exception,
)

__all__ = [
    "FetchResult",
    "build_sse_error_payload",
    "build_timeout_global_error_payload",
    "build_unexpected_error_payload",
    "build_validation_error_payload",
    "classify_fetch_exception",
]
