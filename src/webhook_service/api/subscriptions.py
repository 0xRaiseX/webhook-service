from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.store import models
from .deps import get_db, require_scope
from datetime import datetime

router = APIRouter()


class SubscriptionFilters(BaseModel):
    chain_id: Optional[List[str]] = None
    contract_address: Optional[List[str]] = None
    topic0: Optional[List[str]] = None
    from_address: Optional[List[str]] = None
    to_address: Optional[List[str]] = None
    token_address: Optional[List[str]] = None
    token_id: Optional[List[str]] = None
    abi_event: Optional[str] = None
    args: Optional[Dict[str, Any]] = None


class SubscriptionCreate(BaseModel):
    endpoint_id: str
    event_types: List[str]
    filters: SubscriptionFilters
    confirmations: int = 12
    status: str = "active"


@router.post("", response_model=dict)
async def create_subscription(
    payload: SubscriptionCreate,
    project: models.Project = Depends(require_scope("admin")),
    session: AsyncSession = Depends(get_db),
):
    endpoint = await session.get(models.Endpoint, payload.endpoint_id)
    if not endpoint or endpoint.project_id != project.id:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    sub = models.Subscription(
        id=f"sub_{int(datetime.utcnow().timestamp())}",
        project_id=project.id,
        endpoint_id=payload.endpoint_id,
        event_types=payload.event_types,
        filters=payload.filters.model_dump(),
        confirmations=payload.confirmations,
        status=payload.status,
    )
    session.add(sub)
    await session.commit()
    return {"id": sub.id}


@router.get("", response_model=list)
async def list_subscriptions(
    project: models.Project = Depends(require_scope("read")),
    session: AsyncSession = Depends(get_db),
):
    res = await session.execute(
        models.Subscription.__table__.select().where(models.Subscription.project_id == project.id)
    )
    return [dict(row) for row in res.mappings().all()]


@router.patch("/{subscription_id}", response_model=dict)
async def update_subscription(
    subscription_id: str,
    payload: SubscriptionCreate,
    project: models.Project = Depends(require_scope("admin")),
    session: AsyncSession = Depends(get_db),
):
    sub = await session.get(models.Subscription, subscription_id)
    if not sub or sub.project_id != project.id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    sub.event_types = payload.event_types
    sub.filters = payload.filters.model_dump()
    sub.confirmations = payload.confirmations
    sub.status = payload.status
    sub.endpoint_id = payload.endpoint_id
    sub.updated_at = datetime.utcnow()
    await session.commit()
    return {"id": sub.id}

