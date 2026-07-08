from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..core.store import models
from .deps import get_db, require_scope
from ..core.match.matcher import match_and_enqueue
from ..core.domain.event import CanonicalEvent
from .cursor import encode_cursor, apply_cursor

router = APIRouter()


class EventResponse(BaseModel):
    id: str
    project_id: str
    type: str
    created: datetime
    api_version: str
    source: dict
    data: dict
    links: Optional[dict] = None


class EventListResponse(BaseModel):
    data: List[EventResponse]
    next_cursor: Optional[str] = None


@router.get("", response_model=EventListResponse)
async def list_events(
    project: models.Project = Depends(require_scope("read")),
    session: AsyncSession = Depends(get_db),
    event_type: str | None = Query(default=None, alias="type"),
    limit: int = 100,
    cursor: str | None = Query(default=None),
):
    stmt = select(models.Event).where(models.Event.project_id == project.id).order_by(models.Event.created.desc(), models.Event.id.desc())
    if event_type:
        stmt = stmt.where(models.Event.type == event_type)
    stmt = apply_cursor(stmt, models.Event, cursor)
    stmt = stmt.limit(min(limit, 500))
    res = await session.execute(stmt)
    events = res.scalars().all()
    data = [
        EventResponse.model_validate({k: v for k, v in e.__dict__.items() if not k.startswith("_")})
        for e in events
    ]
    next_cursor = encode_cursor(data[-1].created, data[-1].id) if len(data) == min(limit, 500) and data else None
    return EventListResponse(data=data, next_cursor=next_cursor)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    project: models.Project = Depends(require_scope("read")),
    session: AsyncSession = Depends(get_db),
):
    evt_row = await session.get(models.Event, event_id)
    if not evt_row or evt_row.project_id != project.id:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventResponse.model_validate({k: v for k, v in evt_row.__dict__.items() if not k.startswith("_")})


@router.post("/{event_id}/replay", response_model=dict)
async def replay_event(
    event_id: str,
    project: models.Project = Depends(require_scope("admin")),
    session: AsyncSession = Depends(get_db),
):
    evt_row = await session.get(models.Event, event_id)
    if not evt_row or evt_row.project_id != project.id:
        raise HTTPException(status_code=404, detail="Event not found")
    evt = CanonicalEvent(**{k: v for k, v in evt_row.__dict__.items() if not k.startswith("_")})
    await match_and_enqueue(session, evt)
    return {"status": "enqueued"}

