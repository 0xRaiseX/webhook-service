from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..core.store import models
from .deps import get_db, require_scope
from .cursor import encode_cursor, apply_cursor

router = APIRouter()


class DeliveryResponse(BaseModel):
    delivery_id: str
    project_id: str
    event_id: str
    subscription_id: str
    endpoint_id: str
    attempt: int
    next_attempt_at: datetime
    status: str
    payload_hash: str
    created_at: datetime
    updated_at: datetime


class DeliveryListResponse(BaseModel):
    data: List[DeliveryResponse]
    next_cursor: Optional[str] = None


@router.get("", response_model=DeliveryListResponse)
async def list_deliveries(
    project: models.Project = Depends(require_scope("read")),
    session: AsyncSession = Depends(get_db),
    status: str | None = Query(default=None),
    limit: int = 100,
    cursor: str | None = Query(default=None),
):
    stmt = select(models.Outbox).where(models.Outbox.project_id == project.id).order_by(models.Outbox.created_at.desc(), models.Outbox.delivery_id.desc())
    if status:
        stmt = stmt.where(models.Outbox.status == status)
    stmt = apply_cursor(stmt, models.Outbox, cursor, created_field="created_at", id_field="delivery_id")
    stmt = stmt.limit(min(limit, 500))
    res = await session.execute(stmt)
    tasks = res.scalars().all()
    data = [
        DeliveryResponse.model_validate({k: v for k, v in t.__dict__.items() if not k.startswith("_")})
        for t in tasks
    ]
    next_cursor = encode_cursor(data[-1].created_at, data[-1].delivery_id) if len(data) == min(limit, 500) and data else None
    return DeliveryListResponse(data=data, next_cursor=next_cursor)

