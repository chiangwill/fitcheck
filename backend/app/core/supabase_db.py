from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.config import settings

_SELECT = "id,source,title,company,url,location,salary_min,salary_max,japanese_level,remote_level,sponsors_visas,skills,published_at,first_seen"


def _headers() -> dict:
    return {
        "apikey": settings.supabase_key,
        "Authorization": f"Bearer {settings.supabase_key}",
    }


def _base_url() -> str:
    return f"{settings.supabase_url}/rest/v1"


async def fetch_crawler_jobs(days: int = 7) -> list[dict[str, Any]]:
    """Fetch recent jobs from jp_job_crawler's Supabase table."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_base_url()}/jobs",
            headers=_headers(),
            params={
                "select": _SELECT,
                "first_seen": f"gte.{cutoff}",
                "order": "first_seen.desc",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_all_crawler_jobs() -> list[dict[str, Any]]:
    """Fetch all crawler jobs regardless of age."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_base_url()}/jobs",
            headers=_headers(),
            params={
                "select": _SELECT,
                "order": "first_seen.desc",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_crawler_job_by_id(job_id: str) -> dict[str, Any] | None:
    """Fetch a single crawler job by its Supabase id."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_base_url()}/jobs",
            headers=_headers(),
            params={
                "select": _SELECT,
                "id": f"eq.{job_id}",
                "limit": "1",
            },
            timeout=10,
        )
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else None
