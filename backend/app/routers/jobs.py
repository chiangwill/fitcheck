from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobParseRequest, JobResponse
from app.services.embedder import embed_and_store_job
from app.services.scraper import fetch_and_parse_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def _process_job(job_id: int, url: str, db: AsyncSession):
    try:
        raw_content, parsed = await fetch_and_parse_job(url)
        embed_text = f"{parsed.get('title', '')} {parsed.get('description', '')} {' '.join(parsed.get('required_skills', []))}"
        embedding_id = await embed_and_store_job(job_id, embed_text)
        await db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                title=parsed.get("title"),
                company=parsed.get("company"),
                raw_content=raw_content,
                parsed_json=parsed,
                embedding_id=embedding_id,
            )
        )
        await db.commit()
    except Exception as e:
        print(f"[Job processing error] job_id={job_id}: {e}")


@router.post("/parse", response_model=JobResponse, status_code=201)
async def parse_job(
    payload: JobParseRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # 已存在就直接回傳
    result = await db.execute(select(Job).where(Job.url == payload.url))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    job = Job(url=payload.url)
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(_process_job, job.id, payload.url, db)
    return job


@router.get("", response_model=list[JobResponse])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).order_by(Job.created_at.desc()))
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="找不到職缺")
    return job
