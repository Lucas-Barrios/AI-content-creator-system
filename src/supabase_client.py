"""
Supabase client factory for backend-only operations.

Use this from Python API routes, ingestion jobs, and embedding workers. The
service role key must never be exposed to the Next.js browser client.
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class SupabaseConfigurationError(RuntimeError):
    """Raised when required Supabase environment variables are missing."""


def get_supabase_admin_client() -> Any:
    """Return a Supabase client using the server-only service role key."""
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        raise SupabaseConfigurationError(
            "Supabase backend client is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env."
        )

    try:
        from supabase import create_client
    except ModuleNotFoundError as error:
        raise SupabaseConfigurationError(
            "The Python Supabase client is not installed. Run: pip install -r requirements.txt"
        ) from error

    return create_client(supabase_url, service_role_key)
