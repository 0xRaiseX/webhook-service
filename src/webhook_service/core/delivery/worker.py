import asyncio
from datetime import datetime, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..store import models
from .client import WebhookClient
from .signer import sign_event
from ..domain.event import CanonicalEvent
from ..config import get_settings
from ..security.crypto import decrypt_secret
import orjson
from .. import metrics


class DeliveryWorker:
    def __init__(self, session_factory, settings=None):
        self.session_factory = session_factory
        self.settings = settings or get_settings()
        self.client = WebhookClient(
            max_concurrency_per_endpoint=self.settings.delivery_max_concurrency_per_endpoint
        )
        self.retryable_statuses = {500, 502, 503, 504}
        self.non_retry_statuses = {401, 403, 404, 410}

    async def fetch_batch(self, session: AsyncSession, limit: int = 50):
        stmt = (
            select(models.Outbox)
            .where(models.Outbox.status == "pending", models.Outbox.next_attempt_at <= datetime.utcnow())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        res = await session.execute(stmt)
        return res.scalars().all()

    async def run_once(self, limit: int = 50):
        async with self.session_factory() as session:
            batch = await self.fetch_batch(session, limit)
            for task in batch:
                await self._process_task(session, task)
            await session.commit()

    async def _process_task(self, session: AsyncSession, task: models.Outbox):
        # load event and endpoint
        event_row = await session.get(models.Event, task.event_id)
        endpoint = await session.get(models.Endpoint, task.endpoint_id)
        if not event_row or not endpoint:
            await self._mark_dead(session, task, "missing event or endpoint")
            return

        event_payload = {k: v for k, v in event_row.__dict__.items() if not k.startswith("_")}
        event = CanonicalEvent(**event_payload)
        secret = decrypt_secret(endpoint.secret_enc, self.settings.encryption_key)
        signature_header, ts = sign_event(secret, event, delivery_id=str(task.delivery_id))
        try:
            start = datetime.utcnow()
            resp = await self.client.post(
                endpoint.url,
                payload=event.model_dump(),
                headers={
                    "Webhook-Signature": signature_header,
                    "Webhook-Id": str(task.delivery_id),
                    "Webhook-Timestamp": str(ts),
                },
                endpoint_id=endpoint.id,
            )
            status_code = resp.status_code
            if 200 <= status_code < 300:
                metrics.delivery_success.inc()
                metrics.delivery_latency.observe((datetime.utcnow() - start).total_seconds())
                await self._record_attempt(session, task, status="success", status_code=status_code)
                await session.execute(
                    update(models.Outbox)
                    .where(models.Outbox.delivery_id == task.delivery_id)
                    .values(status="sent", updated_at=datetime.utcnow())
                )
            elif status_code in self.non_retry_statuses:
                metrics.delivery_dead.inc()
                await self._mark_dead(session, task, f"non-retryable: {status_code}")
            else:
                metrics.delivery_retry.inc()
                await self._retry(session, task, f"non-2xx: {status_code}", status_code)
        except Exception as exc:
            metrics.delivery_retry.inc()
            await self._retry(session, task, str(exc))

    async def _record_attempt(
        self, session: AsyncSession, task: models.Outbox, status: str, status_code: int | None = None, error: str | None = None
    ):
        session.add(
            models.DeliveryAttempt(
                delivery_id=task.delivery_id,
                event_id=task.event_id,
                endpoint_id=task.endpoint_id,
                status=status,
                status_code=status_code,
                error=error,
            )
        )

    async def _retry(self, session: AsyncSession, task: models.Outbox, error: str, status_code: int | None = None):
        await self._record_attempt(session, task, status="retry", status_code=status_code, error=error)
        schedule = self.settings.retry_schedule_seconds
        next_attempt = task.attempt + 1
        if next_attempt >= len(schedule):
            await self._mark_dead(session, task, error)
            return
        delay = schedule[next_attempt]
        jitter = random.uniform(0, delay * 0.1)
        next_time = datetime.utcnow() + timedelta(seconds=delay + jitter)
        # max age
        if (next_time - task.created_at).total_seconds() > self.settings.delivery_max_age_seconds:
            await self._mark_dead(session, task, "max age exceeded")
            return
        await session.execute(
            update(models.Outbox)
            .where(models.Outbox.delivery_id == task.delivery_id)
            .values(
                attempt=task.attempt + 1,
                next_attempt_at=next_time,
                updated_at=datetime.utcnow(),
            )
        )

    async def _mark_dead(self, session: AsyncSession, task: models.Outbox, error: str):
        await self._record_attempt(session, task, status="dead", error=error)
        await session.execute(
            update(models.Outbox)
            .where(models.Outbox.delivery_id == task.delivery_id)
            .values(status="dead", updated_at=datetime.utcnow())
        )

    async def loop(self, interval_sec: int = 2):
        while True:
            await self.run_once()
            await asyncio.sleep(interval_sec)


def _decrypt(secret_enc: str, key: str) -> str:
    # placeholder: not real crypto, replace with proper encryption (fernet/libsodium)
    # For MVP we just return the stored secret.
    return secret_enc

