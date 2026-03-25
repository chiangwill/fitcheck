"""
Targeted tests for the crawler jobs integration.

supabase_db.py  — fetch_crawler_jobs, fetch_all_crawler_jobs, fetch_crawler_job_by_id
crawler_jobs.py — list endpoint, score endpoint (all branches)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_httpx_client(return_value=None, side_effect=None):
    """Build a mock httpx.AsyncClient context manager."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    if return_value is not None:
        mock_response.json.return_value = return_value

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    if side_effect:
        mock_client.get.side_effect = side_effect
    else:
        mock_client.get.return_value = mock_response

    return mock_client, mock_response


# ---------------------------------------------------------------------------
# supabase_db: fetch_crawler_jobs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_crawler_jobs_returns_list():
    """fetch_crawler_jobs() calls Supabase PostgREST and returns a list of dicts."""
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
    mock_client, _ = _mock_httpx_client(return_value=[fake_row])

    with patch("app.core.supabase_db.httpx.AsyncClient", return_value=mock_client):
        from app.core.supabase_db import fetch_crawler_jobs
        result = await fetch_crawler_jobs(days=7)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["title"] == "Senior Python Engineer"
    assert result[0]["skills"] == ["Python", "FastAPI", "PostgreSQL"]


@pytest.mark.asyncio
async def test_fetch_crawler_jobs_handles_connection_error():
    """fetch_crawler_jobs() propagates connection errors so the router returns 503."""
    mock_client, _ = _mock_httpx_client(side_effect=Exception("connection refused"))

    with patch("app.core.supabase_db.httpx.AsyncClient", return_value=mock_client):
        from app.core.supabase_db import fetch_crawler_jobs
        with pytest.raises(Exception, match="connection refused"):
            await fetch_crawler_jobs()


# ---------------------------------------------------------------------------
# supabase_db: fetch_all_crawler_jobs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_all_crawler_jobs_returns_list():
    """fetch_all_crawler_jobs() fetches without date filter and returns all rows."""
    fake_rows = [{"id": "1", "title": "Job A"}, {"id": "2", "title": "Job B"}]
    mock_client, _ = _mock_httpx_client(return_value=fake_rows)

    with patch("app.core.supabase_db.httpx.AsyncClient", return_value=mock_client):
        from app.core.supabase_db import fetch_all_crawler_jobs
        result = await fetch_all_crawler_jobs()

    assert len(result) == 2
    assert result[0]["title"] == "Job A"

    # Verify limit=1000 param was passed (prevents Supabase default truncation)
    call_kwargs = mock_client.get.call_args
    assert call_kwargs.kwargs["params"]["limit"] == "1000"


# ---------------------------------------------------------------------------
# supabase_db: fetch_crawler_job_by_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_crawler_job_by_id_found():
    """fetch_crawler_job_by_id() returns the matching row dict."""
    fake_job = {"id": "xyz", "title": "Backend Engineer", "url": "https://japan.dev/jobs/xyz"}
    mock_client, _ = _mock_httpx_client(return_value=[fake_job])

    with patch("app.core.supabase_db.httpx.AsyncClient", return_value=mock_client):
        from app.core.supabase_db import fetch_crawler_job_by_id
        result = await fetch_crawler_job_by_id("xyz")

    assert result is not None
    assert result["id"] == "xyz"
    assert result["title"] == "Backend Engineer"


@pytest.mark.asyncio
async def test_fetch_crawler_job_by_id_not_found():
    """fetch_crawler_job_by_id() returns None when Supabase returns empty list."""
    mock_client, _ = _mock_httpx_client(return_value=[])

    with patch("app.core.supabase_db.httpx.AsyncClient", return_value=mock_client):
        from app.core.supabase_db import fetch_crawler_job_by_id
        result = await fetch_crawler_job_by_id("nonexistent")

    assert result is None


# ---------------------------------------------------------------------------
# router: list_crawler_jobs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_crawler_jobs_returns_recent():
    """GET /crawler-jobs calls fetch_crawler_jobs() (7-day window) by default."""
    fake_jobs = [{"id": "1", "title": "Job A"}]

    with patch("app.routers.crawler_jobs.fetch_crawler_jobs", AsyncMock(return_value=fake_jobs)) as mock_fetch:
        from app.routers.crawler_jobs import list_crawler_jobs
        result = await list_crawler_jobs(all_time=False)

    assert result == fake_jobs
    mock_fetch.assert_called_once()


@pytest.mark.asyncio
async def test_list_crawler_jobs_all_time():
    """GET /crawler-jobs?all_time=true calls fetch_all_crawler_jobs()."""
    fake_jobs = [{"id": "1"}, {"id": "2"}]

    with patch("app.routers.crawler_jobs.fetch_all_crawler_jobs", AsyncMock(return_value=fake_jobs)) as mock_fetch:
        from app.routers.crawler_jobs import list_crawler_jobs
        result = await list_crawler_jobs(all_time=True)

    assert len(result) == 2
    mock_fetch.assert_called_once()


@pytest.mark.asyncio
async def test_list_crawler_jobs_raises_503_on_supabase_error():
    """GET /crawler-jobs returns 503 when Supabase is unreachable."""
    with patch("app.routers.crawler_jobs.fetch_crawler_jobs", AsyncMock(side_effect=Exception("timeout"))):
        from app.routers.crawler_jobs import list_crawler_jobs
        with pytest.raises(HTTPException) as exc_info:
            await list_crawler_jobs(all_time=False)

    assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# router: score_crawler_job — error paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_score_crawler_job_no_active_resume():
    """score endpoint returns 404 when no active resume exists."""
    no_resume_result = MagicMock()
    no_resume_result.scalar_one_or_none = MagicMock(return_value=None)

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=no_resume_result)

    from app.routers.crawler_jobs import score_crawler_job
    with pytest.raises(HTTPException) as exc_info:
        await score_crawler_job("any-id", db=mock_db)

    assert exc_info.value.status_code == 404
    assert "active 履歷" in exc_info.value.detail


@pytest.mark.asyncio
async def test_score_crawler_job_supabase_error_returns_503():
    """score endpoint returns 503 when Supabase fetch fails."""
    resume_result = MagicMock()
    resume_result.scalar_one_or_none = MagicMock(return_value=MagicMock(id=1, raw_text="cv"))

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=resume_result)

    with patch("app.routers.crawler_jobs.fetch_crawler_job_by_id", AsyncMock(side_effect=Exception("Supabase down"))):
        from app.routers.crawler_jobs import score_crawler_job
        with pytest.raises(HTTPException) as exc_info:
            await score_crawler_job("bad-id", db=mock_db)

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_score_crawler_job_not_found_in_supabase():
    """score endpoint returns 404 when job id doesn't exist in Supabase."""
    resume_result = MagicMock()
    resume_result.scalar_one_or_none = MagicMock(return_value=MagicMock(id=1, raw_text="cv"))

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=resume_result)

    with patch("app.routers.crawler_jobs.fetch_crawler_job_by_id", AsyncMock(return_value=None)):
        from app.routers.crawler_jobs import score_crawler_job
        with pytest.raises(HTTPException) as exc_info:
            await score_crawler_job("ghost-id", db=mock_db)

    assert exc_info.value.status_code == 404
    assert "找不到職缺" in exc_info.value.detail


@pytest.mark.asyncio
async def test_score_crawler_job_invalid_url_returns_422():
    """score endpoint returns 422 for jobs with non-https URLs (SSRF guard)."""
    resume_result = MagicMock()
    resume_result.scalar_one_or_none = MagicMock(return_value=MagicMock(id=1, raw_text="cv"))

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=resume_result)

    bad_job = {"id": "x", "url": "http://evil.com/job", "title": "Trap", "company": "Evil"}

    with patch("app.routers.crawler_jobs.fetch_crawler_job_by_id", AsyncMock(return_value=bad_job)):
        from app.routers.crawler_jobs import score_crawler_job
        with pytest.raises(HTTPException) as exc_info:
            await score_crawler_job("x", db=mock_db)

    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# router: score_crawler_job — cache hit (most important: protects Gemini quota)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_score_crawler_job_returns_cached_result_without_calling_gemini():
    """
    If a Match already exists for (job_id, resume_id), return it immediately
    without calling Gemini. Protects the ~20 req/day free tier quota.
    """
    fake_resume = MagicMock(id=1, raw_text="Python developer with 5 years experience", is_active=True)
    fake_local_job = MagicMock(id=10, url="https://japan.dev/jobs/acme",
                               parsed_json={"title": "Python Engineer"})
    fake_cached_match = MagicMock(score=8.5, matched_skills=["Python", "FastAPI"],
                                  missing_skills=["Kubernetes"], suggestion="補強 Kubernetes 技能", id=99)

    fake_crawler_job = {"id": "supabase-abc", "url": "https://japan.dev/jobs/acme",
                        "title": "Python Engineer", "company": "Acme", "source": "japan_dev"}

    resume_result = MagicMock()
    resume_result.scalar_one_or_none = MagicMock(return_value=fake_resume)
    job_result = MagicMock()
    job_result.scalar_one_or_none = MagicMock(return_value=fake_local_job)
    match_result = MagicMock()
    match_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=fake_cached_match)))

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[resume_result, job_result, match_result])

    analyze_mock = AsyncMock()

    with (
        patch("app.routers.crawler_jobs.fetch_crawler_job_by_id", return_value=fake_crawler_job),
        patch("app.routers.crawler_jobs.analyze_match", analyze_mock),
    ):
        from app.routers.crawler_jobs import score_crawler_job
        response = await score_crawler_job("supabase-abc", db=mock_db)

    assert response["score"] == 8.5
    assert response["cached"] is True
    assert response["match_id"] == 99
    analyze_mock.assert_not_called()


# ---------------------------------------------------------------------------
# router: score_crawler_job — new job, calls Gemini
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_score_crawler_job_existing_job_no_parsed_json_retries_parse():
    """
    If a local Job row exists but parsed_json is None (previous parse failed),
    the endpoint retries fetching and parsing, then continues to scoring.
    """
    fake_resume = MagicMock(id=1, raw_text="Python developer", is_active=True)
    # Job exists but parse previously failed
    fake_local_job = MagicMock(id=10, url="https://japan.dev/jobs/retry",
                               parsed_json=None)
    fake_cached_match = MagicMock(score=6.0, matched_skills=["Python"],
                                  missing_skills=[], suggestion="OK", id=77)

    fake_crawler_job = {"id": "retry-id", "url": "https://japan.dev/jobs/retry",
                        "title": "Retry Job", "company": "RetryCo"}

    resume_result = MagicMock()
    resume_result.scalar_one_or_none = MagicMock(return_value=fake_resume)
    job_result = MagicMock()
    job_result.scalar_one_or_none = MagicMock(return_value=fake_local_job)
    match_result = MagicMock()
    match_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=fake_cached_match)))

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[resume_result, job_result, match_result])

    with (
        patch("app.routers.crawler_jobs.fetch_crawler_job_by_id", return_value=fake_crawler_job),
        patch("app.routers.crawler_jobs.fetch_and_parse_job",
              AsyncMock(return_value=(None, {"title": "Retry Job"}))) as mock_parse,
        patch("app.routers.crawler_jobs.analyze_match", AsyncMock()),
    ):
        from app.routers.crawler_jobs import score_crawler_job
        response = await score_crawler_job("retry-id", db=mock_db)

    # Parse was retried and job now has parsed_json set
    mock_parse.assert_called_once()
    assert fake_local_job.parsed_json == {"title": "Retry Job"}
    assert response["cached"] is True
    assert response["score"] == 6.0


@pytest.mark.asyncio
async def test_score_crawler_job_existing_job_retry_parse_fails_returns_422():
    """
    If the retry parse of a previously-unparsed job fails, endpoint returns 422.
    """
    fake_resume = MagicMock(id=1, raw_text="Python developer", is_active=True)
    fake_local_job = MagicMock(id=10, url="https://japan.dev/jobs/broken",
                               parsed_json=None)

    fake_crawler_job = {"id": "broken-id", "url": "https://japan.dev/jobs/broken",
                        "title": "Broken Job", "company": "BrokenCo"}

    resume_result = MagicMock()
    resume_result.scalar_one_or_none = MagicMock(return_value=fake_resume)
    job_result = MagicMock()
    job_result.scalar_one_or_none = MagicMock(return_value=fake_local_job)

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[resume_result, job_result])

    with (
        patch("app.routers.crawler_jobs.fetch_crawler_job_by_id", return_value=fake_crawler_job),
        patch("app.routers.crawler_jobs.fetch_and_parse_job",
              AsyncMock(side_effect=Exception("page not found"))),
    ):
        from app.routers.crawler_jobs import score_crawler_job
        with pytest.raises(HTTPException) as exc_info:
            await score_crawler_job("broken-id", db=mock_db)

    assert exc_info.value.status_code == 422
    assert "解析失敗" in exc_info.value.detail


@pytest.mark.asyncio
async def test_score_crawler_job_new_job_parse_fails_returns_422():
    """
    If fetching/parsing a brand-new job URL fails, endpoint returns 422.
    """
    fake_resume = MagicMock(id=1, raw_text="Python developer", is_active=True)

    fake_crawler_job = {"id": "new-bad", "url": "https://japan.dev/jobs/gone",
                        "title": "Gone Job", "company": "GoneCo"}

    resume_result = MagicMock()
    resume_result.scalar_one_or_none = MagicMock(return_value=fake_resume)
    no_job_result = MagicMock()
    no_job_result.scalar_one_or_none = MagicMock(return_value=None)

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[resume_result, no_job_result])

    with (
        patch("app.routers.crawler_jobs.fetch_crawler_job_by_id", return_value=fake_crawler_job),
        patch("app.routers.crawler_jobs.fetch_and_parse_job",
              AsyncMock(side_effect=Exception("404 not found"))),
    ):
        from app.routers.crawler_jobs import score_crawler_job
        with pytest.raises(HTTPException) as exc_info:
            await score_crawler_job("new-bad", db=mock_db)

    assert exc_info.value.status_code == 422
    assert "解析失敗" in exc_info.value.detail


@pytest.mark.asyncio
async def test_score_crawler_job_gemini_failure_returns_500():
    """
    If Gemini analyze_match raises, endpoint returns 500 (not a crash).
    """
    fake_resume = MagicMock(id=1, raw_text="Python developer", is_active=True)
    fake_local_job = MagicMock(id=10, url="https://japan.dev/jobs/gemini-fail",
                               parsed_json={"title": "Some Job"})

    fake_crawler_job = {"id": "gemini-fail", "url": "https://japan.dev/jobs/gemini-fail",
                        "title": "Some Job", "company": "SomeCo"}

    resume_result = MagicMock()
    resume_result.scalar_one_or_none = MagicMock(return_value=fake_resume)
    job_result = MagicMock()
    job_result.scalar_one_or_none = MagicMock(return_value=fake_local_job)
    no_match_result = MagicMock()
    no_match_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[resume_result, job_result, no_match_result])

    with (
        patch("app.routers.crawler_jobs.fetch_crawler_job_by_id", return_value=fake_crawler_job),
        patch("app.routers.crawler_jobs.analyze_match",
              AsyncMock(side_effect=Exception("429 quota exceeded"))),
    ):
        from app.routers.crawler_jobs import score_crawler_job
        with pytest.raises(HTTPException) as exc_info:
            await score_crawler_job("gemini-fail", db=mock_db)

    assert exc_info.value.status_code == 500
    assert "Gemini" in exc_info.value.detail


@pytest.mark.asyncio
async def test_score_crawler_job_new_job_calls_gemini_and_saves_match():
    """
    When no local job or cached match exists, the endpoint fetches+parses the
    job page, calls Gemini, saves a Match, and returns cached=False.
    """
    fake_resume = MagicMock(id=1, raw_text="Python developer", is_active=True)
    fake_new_job = MagicMock(id=20, url="https://japan.dev/jobs/new",
                             parsed_json={"title": "New Job"})
    fake_new_match = MagicMock(score=7.0, matched_skills=["Python"],
                               missing_skills=[], suggestion="Good fit", id=55)

    fake_crawler_job = {"id": "new-id", "url": "https://japan.dev/jobs/new",
                        "title": "New Job", "company": "NewCo", "source": "japan_dev"}

    gemini_result = {"score": 7.0, "matched_skills": ["Python"],
                     "missing_skills": [], "suggestion": "Good fit"}

    resume_result = MagicMock()
    resume_result.scalar_one_or_none = MagicMock(return_value=fake_resume)

    # No local job found
    no_job_result = MagicMock()
    no_job_result.scalar_one_or_none = MagicMock(return_value=None)

    # No cached match
    no_match_result = MagicMock()
    no_match_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[resume_result, no_job_result, no_match_result])
    mock_db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, "id", 55) or obj)

    analyze_mock = AsyncMock(return_value=gemini_result)

    with (
        patch("app.routers.crawler_jobs.fetch_crawler_job_by_id", return_value=fake_crawler_job),
        patch("app.routers.crawler_jobs.fetch_and_parse_job", AsyncMock(return_value=(None, {"title": "New Job"}))),
        patch("app.routers.crawler_jobs.analyze_match", analyze_mock),
    ):
        from app.routers.crawler_jobs import score_crawler_job
        response = await score_crawler_job("new-id", db=mock_db)

    assert response["cached"] is False
    assert response["score"] == 7.0
    analyze_mock.assert_called_once()
