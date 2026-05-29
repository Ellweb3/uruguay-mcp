"""Runtime configuration, sourced from environment variables (prefix ``URUGUAY_MCP_``)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings for the server.

    Every field can be overridden via an environment variable, e.g.
    ``URUGUAY_MCP_LANG=en`` or ``URUGUAY_MCP_HTTP_TIMEOUT=30``.
    """

    model_config = SettingsConfigDict(env_prefix="URUGUAY_MCP_", extra="ignore")

    # Default response language for human-facing strings (errors, descriptions).
    # Uruguay's data is Spanish-first; English is offered as a courtesy.
    lang: str = "es"

    # HTTP behaviour, shared by every async client.
    http_timeout: float = 30.0
    http_max_retries: int = 3
    user_agent: str = "uruguay-mcp/0.1 (+https://github.com/uruguay-mcp)"

    # Cache: time-to-live in seconds for cached API responses.
    cache_ttl: int = 900

    # Token-bucket rate limiting (requests per second, per host).
    rate_limit_rps: float = 5.0

    # Comma-separated module allowlist; empty means "load all".
    modules: str = ""

    def enabled_modules(self) -> set[str] | None:
        names = {m.strip() for m in self.modules.split(",") if m.strip()}
        return names or None


settings = Settings()
