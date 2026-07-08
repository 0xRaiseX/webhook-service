from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt
from ..db import get_session
from ..core.store import models
from .ratelimit import rate_limit

security = HTTPBearer(auto_error=True)


async def get_db() -> AsyncSession:
    async for session in get_session():
        yield session


def hash_key(key: str) -> str:
    # bcrypt includes salt; use for storage
    return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()


def verify_key(key: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(key.encode(), hashed.encode())
    except ValueError:
        return False


async def get_current_project(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> models.Project:
    token = credentials.credentials
    res = await session.execute(
        select(models.ApiKey).where(models.ApiKey.revoked_at.is_(None))
    )
    candidates = res.scalars().all()
    api_key = next((k for k in candidates if verify_key(token, k.key_hash)), None)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    project = await session.get(models.Project, api_key.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid project")
    # attach scopes for downstream checks
    project._scopes = api_key.scopes  # type: ignore[attr-defined]
    rate_limit(project.id)
    return project


def require_scope(scope: str):
    async def dependency(project: models.Project = Depends(get_current_project)) -> models.Project:
        scopes = getattr(project, "_scopes", []) or []
        if scope not in scopes and "admin" not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return project

    return dependency
