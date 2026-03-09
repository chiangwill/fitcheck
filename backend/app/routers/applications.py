from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.application import Application
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationUpdate

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(payload: ApplicationCreate, db: AsyncSession = Depends(get_db)):
    app = Application(job_id=payload.job_id, match_id=payload.match_id)
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Application).order_by(Application.updated_at.desc()))
    return result.scalars().all()


@router.put("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: int, payload: ApplicationUpdate, db: AsyncSession = Depends(get_db)
):
    app = await db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="找不到投遞紀錄")
    if payload.status is not None:
        app.status = payload.status
    if payload.notes is not None:
        app.notes = payload.notes
    if payload.applied_at is not None:
        app.applied_at = payload.applied_at
    await db.commit()
    await db.refresh(app)
    return app


@router.delete("/{app_id}", status_code=204)
async def delete_application(app_id: int, db: AsyncSession = Depends(get_db)):
    app = await db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="找不到投遞紀錄")
    await db.delete(app)
    await db.commit()
