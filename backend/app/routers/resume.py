from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.match import Match
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeResponse, ResumeUpdate
from app.services.embedder import delete_resume_embedding, embed_and_store_resume
from app.services.parser import extract_text_from_pdf, parse_resume_to_structured

router = APIRouter(prefix="/resume", tags=["resume"])


async def _process_resume(resume_id: int, raw_text: str, db: AsyncSession):
    """背景任務：解析結構化資料 + 生成 Embedding"""
    try:
        parsed = await parse_resume_to_structured(raw_text)
        embedding_id = await embed_and_store_resume(resume_id, raw_text)
        await db.execute(
            update(Resume)
            .where(Resume.id == resume_id)
            .values(parsed_json=parsed, embedding_id=embedding_id)
        )
        await db.commit()
    except Exception as e:
        print(f"[Resume processing error] resume_id={resume_id}: {e}")


@router.post("", response_model=ResumeResponse, status_code=201)
async def create_resume(
    payload: ResumeCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    resume = Resume(version_name=payload.version_name, raw_text=payload.raw_text)
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    background_tasks.add_task(_process_resume, resume.id, resume.raw_text, db)
    return resume


@router.post("/upload", response_model=ResumeResponse, status_code=201)
async def upload_resume_pdf(
    version_name: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支援 PDF 檔案")
    file_bytes = await file.read()
    raw_text = extract_text_from_pdf(file_bytes)
    if not raw_text:
        raise HTTPException(status_code=400, detail="無法從 PDF 解析文字")

    resume = Resume(version_name=version_name, raw_text=raw_text)
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    background_tasks.add_task(_process_resume, resume.id, resume.raw_text, db)
    return resume


@router.get("", response_model=ResumeResponse)
async def get_active_resume(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.is_active == True))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="尚未設定 active 履歷")
    return resume


@router.get("/versions", response_model=list[ResumeResponse])
async def list_resume_versions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).order_by(Resume.created_at.desc()))
    return result.scalars().all()


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="找不到履歷")
    return resume


@router.put("/active/{resume_id}", response_model=ResumeResponse)
async def set_active_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="找不到履歷")

    # 取消所有 active
    await db.execute(update(Resume).values(is_active=False))
    resume.is_active = True
    await db.commit()
    await db.refresh(resume)
    return resume


@router.patch("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: int,
    payload: ResumeUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="找不到履歷")

    if payload.version_name is not None:
        resume.version_name = payload.version_name
    if payload.raw_text is not None:
        # 刪除舊 embedding
        if resume.embedding_id:
            await delete_resume_embedding(resume.embedding_id)
        resume.raw_text = payload.raw_text
        resume.parsed_json = None
        resume.embedding_id = None
        background_tasks.add_task(_process_resume, resume.id, resume.raw_text, db)

    await db.commit()
    await db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="找不到履歷")
    if resume.embedding_id:
        await delete_resume_embedding(resume.embedding_id)
    # 先刪關聯的 matches
    await db.execute(delete(Match).where(Match.resume_id == resume_id))
    await db.delete(resume)
    await db.commit()
