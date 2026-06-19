from functools import lru_cache
from pathlib import Path

import os
from dotenv import load_dotenv
from supabase import Client, create_client

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _load_env() -> None:
    load_dotenv(ENV_PATH, override=True)


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    _load_env()
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in backend/.env")

    return create_client(url, key)


class _SupabaseProxy:
    """Lazy Supabase client so .env updates are picked up after restart."""

    def __getattr__(self, name: str):
        return getattr(get_supabase(), name)


supabase = _SupabaseProxy()
