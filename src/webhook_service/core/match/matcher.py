import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..store import models
from ..domain.event import CanonicalEvent


def payload_hash(event: CanonicalEvent) -> str:
    return hashlib.sha256(event.model_dump_json().encode()).hexdigest()


async def match_and_enqueue(
    session: AsyncSession,
    event: CanonicalEvent,
):
    # prefilter subscriptions
    async with session.begin():
        stmt = select(models.Subscription).where(
            models.Subscription.project_id == event.project_id,
            models.Subscription.status == "active",
        )
        subs = (await session.execute(stmt)).scalars().all()
        tasks = 0
        for sub in subs:
            if event.type not in sub.event_types:
                continue
            filters = sub.filters or {}
            if not _match_filters(event, filters):
                continue
            session.add(
                models.Outbox(
                    project_id=sub.project_id,
                    event_id=event.id,
                    subscription_id=sub.id,
                    endpoint_id=sub.endpoint_id,
                    payload_hash=payload_hash(event),
                )
            )
            tasks += 1
        return tasks


def _match_filters(event: CanonicalEvent, filters: dict) -> bool:
    src = event.source
    data = event.data.normalized
    if "chain_id" in filters and src.chain_id not in filters["chain_id"]:
        return False
    if "contract_address" in filters and src.contract_address not in filters["contract_address"]:
        return False
    if "from" in filters and data.get("from") not in filters["from"]:
        return False
    if "to" in filters and data.get("to") not in filters["to"]:
        return False
    if "token_address" in filters and data.get("token_address") not in filters["token_address"]:
        return False
    return True

