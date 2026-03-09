from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import Job
from app.models.match import Match
from app.models.resume import Resume
from app.schemas.match import MatchResponse
from app.services.matcher import analyze_match

router = APIRouter(prefix="/match", tags=["match"])


@router.post("/{job_id}", response_model=MatchResponse, status_code=201)
async def create_match(job_id: int, db: AsyncSession = Depends(get_db)):
    # 取得 active resume
    result = await db.execute(select(Resume).where(Resume.is_active == True))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="尚未設定 active 履歷")

    # 取得職缺
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="找不到職缺")
    if not job.parsed_json:
        raise HTTPException(status_code=422, detail="職缺尚未解析完成，請稍後再試")

    # 執行分析
    try:
        result_data = await analyze_match(resume.raw_text, job.parsed_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失敗：{e}")

    match = Match(
        resume_id=resume.id,
        job_id=job_id,
        score=result_data.get("score"),
        matched_skills=result_data.get("matched_skills"),
        missing_skills=result_data.get("missing_skills"),
        suggestion=result_data.get("suggestion"),
    )
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="找不到分析結果")
    return match


@router.get("", response_model=list[MatchResponse])
async def list_matches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).order_by(Match.created_at.desc()))
    return result.scalars().all()
