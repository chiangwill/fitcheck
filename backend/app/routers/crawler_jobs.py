from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supabase_db import batch_fetch_crawler_jobs, fetch_all_crawler_jobs, fetch_crawler_job_by_id, fetch_crawler_jobs
from app.database import get_db
from app.models.crawler_job_status import CrawlerJobStatus
from app.models.job import Job
from app.models.match import Match
from app.models.resume import Resume
from app.services.matcher import analyze_match
from app.services.scraper import fetch_and_parse_job

router = APIRouter(prefix="/crawler-jobs", tags=["crawler-jobs"])


class BatchScoreRequest(BaseModel):
    ids: list[str]


class StatusRequest(BaseModel):
    status: str


@router.get("")
async def list_crawler_jobs(all_time: bool = False):
    """Fetch jobs from jp_job_crawler's Supabase table."""
    try:
        if all_time:
            return await fetch_all_crawler_jobs()
        return await fetch_crawler_jobs()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Supabase 連線失敗：{e}")


@router.post("/scores")
async def batch_get_scores(body: BatchScoreRequest, db: AsyncSession = Depends(get_db)):
    """
    Return cached scores for a list of Supabase job IDs.

    IDs with no cached Match for the active resume are omitted from the response.
    Three DB round-trips total (not N+1): Supabase batch → local Job → local Match.
    """
    if not body.ids:
        return {}
    if len(body.ids) > 500:
        raise HTTPException(status_code=422, detail="Too many IDs (max 500)")

    result = await db.execute(select(Resume).where(Resume.is_active == True))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="尚未設定 active 履歷")

    try:
        supabase_jobs = await batch_fetch_crawler_jobs(body.ids)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Supabase 連線失敗：{e}")

    if not supabase_jobs:
        return {}

    url_to_id: dict[str, str] = {j["url"]: j["id"] for j in supabase_jobs if j.get("url")}
    urls = list(url_to_id.keys())
    if not urls:
        return {}

    job_rows = await db.execute(select(Job).where(Job.url.in_(urls)))
    local_jobs = {j.url: j for j in job_rows.scalars().all()}
    if not local_jobs:
        return {}

    local_job_ids = [j.id for j in local_jobs.values()]
    match_rows = await db.execute(
        select(Match)
        .where(Match.job_id.in_(local_job_ids))
        .where(Match.resume_id == resume.id)
        .order_by(Match.created_at.desc())
    )
    job_id_to_match: dict[int, Match] = {}
    for m in match_rows.scalars().all():
        if m.job_id not in job_id_to_match:
            job_id_to_match[m.job_id] = m

    scores: dict[str, dict] = {}
    for url, local_job in local_jobs.items():
        match = job_id_to_match.get(local_job.id)
        if match:
            supabase_id = url_to_id[url]
            raw_missing = match.missing_skills
            if isinstance(raw_missing, dict):
                missing_skills = list(raw_missing.values())
            else:
                missing_skills = raw_missing or []
            scores[supabase_id] = {
                "score": match.score,
                "missing_skills": missing_skills,
                "cached": True,
            }
    return scores


@router.get("/statuses")
async def get_statuses(ids: str = "", db: AsyncSession = Depends(get_db)):
    """
    Return known CrawlerJobStatus rows for the requested Supabase job IDs.

    Pass ?ids=id1,id2,id3 — IDs with no status row are omitted from the response.
    """
    if not ids:
        return {}
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    if not id_list:
        return {}
    if len(id_list) > 500:
        raise HTTPException(status_code=422, detail="Too many IDs (max 500)")

    rows = await db.execute(
        select(CrawlerJobStatus).where(CrawlerJobStatus.supabase_job_id.in_(id_list))
    )
    return {row.supabase_job_id: row.status for row in rows.scalars().all()}


@router.delete("/{supabase_job_id}/status", status_code=204)
async def clear_job_status(supabase_job_id: str, db: AsyncSession = Depends(get_db)):
    """Remove the user-facing status for a crawler job (toggle-off)."""
    row = await db.get(CrawlerJobStatus, supabase_job_id)
    if row:
        await db.delete(row)
        await db.commit()


@router.patch("/{supabase_job_id}/status")
async def set_job_status(
    supabase_job_id: str, body: StatusRequest, db: AsyncSession = Depends(get_db)
):
    """Upsert the user-facing status for a crawler job."""
    allowed = {"interested", "applied", "rejected"}
    if body.status not in allowed:
        raise HTTPException(status_code=422, detail=f"status must be one of {sorted(allowed)}")

    row = CrawlerJobStatus(supabase_job_id=supabase_job_id, status=body.status)
    await db.merge(row)
    await db.commit()
    return {"supabase_job_id": supabase_job_id, "status": body.status}


@router.post("/{supabase_job_id}/score")
async def score_crawler_job(supabase_job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Score a crawler job against the active resume.

    Flow:
    1. Fetch job from Supabase by id
    2. Import to fitcheck's local jobs table if not already there (triggers Gemini parse)
    3. Return cached match if already scored with this resume
    4. Otherwise run Gemini analysis and save result
    """
    # Active resume
    result = await db.execute(select(Resume).where(Resume.is_active == True))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="尚未設定 active 履歷")

    # Fetch job from Supabase
    try:
        crawler_job = await fetch_crawler_job_by_id(supabase_job_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Supabase 連線失敗：{e}")

    if not crawler_job:
        raise HTTPException(status_code=404, detail="找不到職缺")

    url = crawler_job["url"]
    if not url or not url.startswith("https://"):
        raise HTTPException(status_code=422, detail="職缺 URL 格式不合法")

    # Check if already imported to fitcheck's local DB
    result = await db.execute(select(Job).where(Job.url == url))
    local_job = result.scalar_one_or_none()

    if local_job and not local_job.parsed_json:
        # Exists but parse failed previously — retry
        try:
            _, parsed = await fetch_and_parse_job(url)
            local_job.parsed_json = parsed
            await db.commit()
            await db.refresh(local_job)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"職缺頁面解析失敗：{e}")

    if not local_job:
        # First time seeing this URL — fetch and parse the job page
        try:
            _, parsed = await fetch_and_parse_job(url)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"職缺頁面解析失敗：{e}")
        local_job = Job(
            url=url,
            title=crawler_job.get("title"),
            company=crawler_job.get("company"),
            parsed_json=parsed,
        )
        db.add(local_job)
        await db.commit()
        await db.refresh(local_job)

    # Return cached match if this resume already scored this job
    result = await db.execute(
        select(Match)
        .where(Match.job_id == local_job.id)
        .where(Match.resume_id == resume.id)
        .order_by(Match.created_at.desc())
    )
    cached = result.scalars().first()
    if cached:
        return {
            "score": cached.score,
            "matched_skills": cached.matched_skills,
            "missing_skills": cached.missing_skills,
            "suggestion": cached.suggestion,
            "cached": True,
            "match_id": cached.id,
        }

    # Run Gemini analysis
    try:
        result_data = await analyze_match(resume.raw_text, local_job.parsed_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini 分析失敗：{e}")

    match = Match(
        resume_id=resume.id,
        job_id=local_job.id,
        score=result_data.get("score"),
        matched_skills=result_data.get("matched_skills"),
        missing_skills=result_data.get("missing_skills"),
        suggestion=result_data.get("suggestion"),
    )
    db.add(match)
    await db.commit()
    await db.refresh(match)

    return {
        "score": match.score,
        "matched_skills": match.matched_skills,
        "missing_skills": match.missing_skills,
        "suggestion": match.suggestion,
        "cached": False,
        "match_id": match.id,
    }
