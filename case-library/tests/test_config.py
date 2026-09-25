"""Tests for scripts.config: reading the Case Library's settings from the environment."""

import pytest

from scripts.config import (
    NCBI_RATE_LIMIT_WITH_KEY,
    NCBI_RATE_LIMIT_WITHOUT_KEY,
    ConfigError,
    Settings,
    load_settings,
    ncbi_rate_limit,
    require_db_url,
)

DB_URL = "postgresql://casevault_ro:s3cret@db.example.invalid:5432/postgres"
API_KEY = "abc123-not-a-real-key"


def test_load_settings_reads_all_three_keys() -> None:
    settings = load_settings(
        {
            "CASE_VAULT_DB_URL_READONLY": DB_URL,
            "NCBI_API_KEY": API_KEY,
            "NCBI_EMAIL": "curator@example.org",
        }
    )

    assert settings == Settings(
        db_url_readonly=DB_URL, ncbi_api_key=API_KEY, ncbi_email="curator@example.org"
    )


def test_empty_and_blank_values_count_as_unset() -> None:
    settings = load_settings(
        {"CASE_VAULT_DB_URL_READONLY": "", "NCBI_API_KEY": "   ", "NCBI_EMAIL": ""}
    )

    assert settings == Settings(db_url_readonly=None, ncbi_api_key=None, ncbi_email=None)


def test_missing_keys_count_as_unset() -> None:
    assert load_settings({}) == Settings(db_url_readonly=None, ncbi_api_key=None, ncbi_email=None)


def test_values_are_stripped() -> None:
    settings = load_settings({"NCBI_EMAIL": "  curator@example.org\n"})

    assert settings.ncbi_email == "curator@example.org"


def test_malformed_email_is_rejected() -> None:
    with pytest.raises(ConfigError, match="NCBI_EMAIL"):
        load_settings({"NCBI_EMAIL": "not-an-email"})


def test_db_url_must_be_postgres() -> None:
    with pytest.raises(ConfigError, match="CASE_VAULT_DB_URL_READONLY"):
        load_settings({"CASE_VAULT_DB_URL_READONLY": "mysql://x@y/z"})


def test_require_db_url_returns_the_url() -> None:
    settings = load_settings({"CASE_VAULT_DB_URL_READONLY": DB_URL})

    assert require_db_url(settings) == DB_URL


def test_require_db_url_explains_what_is_missing() -> None:
    with pytest.raises(ConfigError, match=r"CASE_VAULT_DB_URL_READONLY.*\.env"):
        require_db_url(load_settings({}))


def test_ncbi_rate_limit_depends_on_the_api_key() -> None:
    with_key = load_settings({"NCBI_API_KEY": API_KEY})
    without_key = load_settings({})

    assert ncbi_rate_limit(with_key) == NCBI_RATE_LIMIT_WITH_KEY == 10
    assert ncbi_rate_limit(without_key) == NCBI_RATE_LIMIT_WITHOUT_KEY == 3


def test_repr_hides_secrets() -> None:
    settings = load_settings({"CASE_VAULT_DB_URL_READONLY": DB_URL, "NCBI_API_KEY": API_KEY})

    text = repr(settings)
    assert "s3cret" not in text
    assert API_KEY not in text


def test_settings_are_immutable() -> None:
    settings = load_settings({})

    with pytest.raises(AttributeError):
        settings.ncbi_email = "x@example.org"  # type: ignore[misc]
