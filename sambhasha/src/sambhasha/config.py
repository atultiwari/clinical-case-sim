"""Settings read from the environment (`.env.example` lists them)."""

import os
from typing import Final

# Sambhasha's own local database from `supabase db start` (ports 563xx).
LOCAL_DB_URL: Final = "postgresql://postgres:postgres@127.0.0.1:56322/postgres"


def database_url() -> str:
    """The run database: SUPABASE_DB_URL if set, otherwise the local database."""
    return os.environ.get("SUPABASE_DB_URL") or LOCAL_DB_URL
