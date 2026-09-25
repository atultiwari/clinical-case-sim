"""Settings for the Case Library scripts, read from the environment.

The keys are listed in `.env.example`. Scripts only read the Case Vault, through
the read-only role; all writes go through the Supabase MCP (CLAUDE.md).
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

DB_URL_KEY = "CASE_VAULT_DB_URL_READONLY"
NCBI_API_KEY_KEY = "NCBI_API_KEY"
NCBI_EMAIL_KEY = "NCBI_EMAIL"

POSTGRES_SCHEMES = ("postgresql://", "postgres://")

# NCBI E-utilities limits, in requests per second.
NCBI_RATE_LIMIT_WITH_KEY = 10
NCBI_RATE_LIMIT_WITHOUT_KEY = 3


class ConfigError(ValueError):
    """A setting is missing or malformed. The message says which and how to fix it."""


@dataclass(frozen=True)
class Settings:
    db_url_readonly: str | None = field(repr=False)
    ncbi_api_key: str | None = field(repr=False)
    ncbi_email: str | None


def _read(env: Mapping[str, str], key: str) -> str | None:
    value = env.get(key, "").strip()
    return value or None


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Read and validate the settings from `env` (default: the process environment)."""
    source = os.environ if env is None else env
    db_url = _read(source, DB_URL_KEY)
    email = _read(source, NCBI_EMAIL_KEY)

    if db_url is not None and not db_url.startswith(POSTGRES_SCHEMES):
        raise ConfigError(f"{DB_URL_KEY} must be a postgresql:// connection URL.")
    if email is not None and "@" not in email:
        raise ConfigError(f"{NCBI_EMAIL_KEY} must be an email address.")

    return Settings(
        db_url_readonly=db_url,
        ncbi_api_key=_read(source, NCBI_API_KEY_KEY),
        ncbi_email=email,
    )


def require_db_url(settings: Settings) -> str:
    """Return the read-only Case Vault URL, or explain how to set it."""
    if settings.db_url_readonly is None:
        raise ConfigError(
            f"{DB_URL_KEY} is not set. Copy .env.example to .env and fill it in, "
            "then run the script with `uv run --env-file .env ...`."
        )
    return settings.db_url_readonly


def ncbi_rate_limit(settings: Settings) -> int:
    """Requests per second allowed by NCBI for these settings."""
    if settings.ncbi_api_key is None:
        return NCBI_RATE_LIMIT_WITHOUT_KEY
    return NCBI_RATE_LIMIT_WITH_KEY
