from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import Job
from app.models.match import Match
from app.models.resume import Resume
from app.schemas.generate import GenerateRequest
from app.schemas.match import MatchResponse
from app.services.generator import generate_cover_letter

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/{match_id}", response_model=MatchResponse)
async def generate(
    match_id: int,
    payload: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="找不到分析結果")

    resume = await db.get(Resume, match.resume_id)
    job = await db.get(Job, match.job_id)
    if not resume or not job or not job.parsed_json:
        raise HTTPException(status_code=422, detail="履歷或職缺資料不完整")

    try:
        zh, en = await generate_cover_letter(resume.raw_text, job.parsed_json, payload.tone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失敗：{e}")

    await db.execute(
        update(Match).where(Match.id == match_id).values(
            cover_letter=zh,
            cover_letter_en=en,
        )
    )
    await db.commit()
    await db.refresh(match)
    return match
