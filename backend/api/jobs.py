from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from storage.database import get_db
from models.db import Job, Event

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{repo_id}")
async def get_jobs(repo_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(Job)
        .where(Job.repo_id == repo_id)
        .order_by(Job.created_at.desc())
        .limit(10)
    )
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "job_type": j.job_type,
            "status": j.status,
            "stage": j.stage,
            "progress": j.progress,
            "error_message": j.error_message,
            "started_at": j.started_at,
            "ended_at": j.ended_at,
        }
        for j in jobs
    ]


@router.get("/{repo_id}/events")
async def get_events(repo_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(Event)
        .where(Event.repo_id == repo_id)
        .order_by(Event.created_at.desc())
        .limit(50)
    )
    events = result.scalars().all()
    return [{"event_type": e.event_type, "data": e.data, "at": e.created_at} for e in events]

