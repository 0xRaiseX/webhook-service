from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.store import models
from .deps import get_db, get_current_project
from datetime import datetime
from ..core.security.crypto import encrypt_secret
from ..config import get_settings
from .deps import require_scope

router = APIRouter()


class EndpointCreate(BaseModel):
    url: HttpUrl
    secret: str
    rate_limit_rps: int | None = None


@router.post("", response_model=dict)
async def create_endpoint(
    payload: EndpointCreate,
    project: models.Project = Depends(require_scope("admin")),
    session: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    endpoint = models.Endpoint(
        id=f"ep_{int(datetime.utcnow().timestamp())}",
        project_id=project.id,
        url=str(payload.url),
        secret_enc=encrypt_secret(payload.secret, settings.encryption_key),
        status="active",
        rate_limit_rps=payload.rate_limit_rps,
    )
    session.add(endpoint)
    await session.commit()
    return {"id": endpoint.id}


@router.patch("/{endpoint_id}", response_model=dict)
async def update_endpoint(
    endpoint_id: str,
    payload: EndpointCreate,
    project: models.Project = Depends(require_scope("admin")),
    session: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    endpoint = await session.get(models.Endpoint, endpoint_id)
    if not endpoint or endpoint.project_id != project.id:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    endpoint.url = str(payload.url)
    endpoint.secret_enc = encrypt_secret(payload.secret, settings.encryption_key)
    endpoint.rate_limit_rps = payload.rate_limit_rps
    endpoint.updated_at = datetime.utcnow()
    await session.commit()
    return {"id": endpoint.id}

