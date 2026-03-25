from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supabase_db import fetch_all_crawler_jobs, fetch_crawler_job_by_id, fetch_crawler_jobs
from app.database import get_db
from app.models.job import Job
from app.models.match import Match
from app.models.resume import Resume
from app.services.matcher import analyze_match
from app.services.scraper import fetch_and_parse_job

router = APIRouter(prefix="/crawler-jobs", tags=["crawler-jobs"])


@router.get("")
async def list_crawler_jobs(all_time: bool = False):
    """Fetch jobs from jp_job_crawler's Supabase table."""
    try:
        if all_time:
            return await fetch_all_crawler_jobs()
        return await fetch_crawler_jobs()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Supabase 連線失敗：{e}")


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
