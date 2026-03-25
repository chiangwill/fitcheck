"""
Targeted tests for the crawler jobs integration.

Test 1: Supabase connection — verifies asyncpg connects and returns data
Test 2: Score caching — verifies a second score call uses cache, not Gemini
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Test 1: Supabase connection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_crawler_jobs_returns_list():
    """
    fetch_crawler_jobs() connects to Supabase and returns a list of dicts.
    Uses a mock connection so this runs without a real Supabase URL.
    """
    fake_row = {
        "id": "abc123",
        "source": "japan_dev",
        "title": "Senior Python Engineer",
        "company": "Acme Corp",
        "url": "https://japan.dev/jobs/acme-senior-python",
        "location": "Tokyo",
        "salary_min": 6000000,
        "salary_max": 9000000,
        "japanese_level": "japanese_level_not_required",
        "remote_level": "remote_level_full",
        "sponsors_visas": True,
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "published_at": None,
        "first_seen": None,
    }

    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[fake_row])
    mock_conn.close = AsyncMock()

    with patch("app.core.supabase_db.asyncpg.connect", return_value=mock_conn):
        from app.core.supabase_db import fetch_crawler_jobs
        result = await fetch_crawler_jobs(days=7)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["title"] == "Senior Python Engineer"
    assert result[0]["skills"] == ["Python", "FastAPI", "PostgreSQL"]
    mock_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_crawler_jobs_handles_connection_error():
    """
    fetch_crawler_jobs() propagates connection errors so the router
    can return a 503 instead of crashing the process.
    """
    with patch(
        "app.core.supabase_db.asyncpg.connect",
        side_effect=Exception("connection refused"),
    ):
        from app.core.supabase_db import fetch_crawler_jobs
        with pytest.raises(Exception, match="connection refused"):
            await fetch_crawler_jobs()


# ---------------------------------------------------------------------------
# Test 2: Score caching
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_score_crawler_job_returns_cached_result_without_calling_gemini():
    """
    If a Match record already exists for (job_id, resume_id), the score
    endpoint returns it immediately without calling Gemini (analyze_match).

    This is the most important test: it prevents double-spending the
    ~20 req/day Gemini free tier quota on jobs already scored.
    """
    from fastapi.testclient import TestClient
    from unittest.mock import patch, AsyncMock, MagicMock

    # Build minimal fake objects
    fake_resume = MagicMock()
    fake_resume.id = 1
    fake_resume.raw_text = "Python developer with 5 years experience"
    fake_resume.is_active = True

    fake_local_job = MagicMock()
    fake_local_job.id = 10
    fake_local_job.url = "https://japan.dev/jobs/acme"
    fake_local_job.parsed_json = {"title": "Python Engineer", "required_skills": ["Python"]}

    fake_cached_match = MagicMock()
    fake_cached_match.score = 8.5
    fake_cached_match.matched_skills = ["Python", "FastAPI"]
    fake_cached_match.missing_skills = ["Kubernetes"]
    fake_cached_match.suggestion = "補強 Kubernetes 技能"
    fake_cached_match.id = 99

    fake_crawler_job = {
        "id": "supabase-abc",
        "url": "https://japan.dev/jobs/acme",
        "title": "Python Engineer",
        "company": "Acme",
        "source": "japan_dev",
        "skills": ["Python"],
    }

    # Mock DB session to return resume, job, and cached match
    mock_db = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        # Detect which query is being executed by the statement's string repr
        stmt_str = str(stmt)
        if "resume" in stmt_str.lower() or "is_active" in stmt_str.lower():
            result.scalar_one_or_none = MagicMock(return_value=fake_resume)
        elif "match" in stmt_str.lower():
            result.scalar_one_or_none = MagicMock(return_value=fake_cached_match)
        else:
            result.scalar_one_or_none = MagicMock(return_value=fake_local_job)
        return result

    mock_db.execute = mock_execute

    analyze_mock = AsyncMock()

    with (
        patch("app.routers.crawler_jobs.fetch_crawler_job_by_id", return_value=fake_crawler_job),
        patch("app.routers.crawler_jobs.analyze_match", analyze_mock),
    ):
        from app.routers.crawler_jobs import score_crawler_job
        response = await score_crawler_job("supabase-abc", db=mock_db)

    # Score returned from cache
    assert response["score"] == 8.5
    assert response["cached"] is True
    assert response["match_id"] == 99

    # Gemini was NOT called
    analyze_mock.assert_not_called()
