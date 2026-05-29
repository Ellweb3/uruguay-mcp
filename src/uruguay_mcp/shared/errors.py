"""Typed errors with bilingual, user-facing messages."""

from __future__ import annotations

from .i18n import t


class UruMcpError(Exception):
    """Base class for all errors surfaced to the model.

    ``code`` is a stable machine-readable identifier; ``message`` is a
    human-facing string already localized for the active language.
    """

    code: str = "error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UpstreamError(UruMcpError):
    """A government API returned an error or was unreachable."""

    code = "upstream_error"


class NotFoundError(UruMcpError):
    """A requested resource (dataset, currency, line...) does not exist."""

    code = "not_found"


class ValidationError(UruMcpError):
    """Caller-supplied arguments are invalid."""

    code = "validation_error"


class RateLimitError(UpstreamError):
    """The upstream API rejected us for sending requests too quickly."""

    code = "rate_limited"


def upstream(api: str, detail: str, *, status: int | None = None) -> UpstreamError:
    """Build an :class:`UpstreamError` with a localized message."""
    msg = t("error.upstream", api=api, detail=detail)
    return UpstreamError(msg, details={"api": api, "status": status})
