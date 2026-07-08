import asyncio
from datetime import datetime, timedelta
from ..db import SessionLocal
from ..config import get_settings
from ..core.store import models
from sqlalchemy import delete


async def run_retention():
    settings = get_settings()
    cutoff = datetime.utcnow() - timedelta(days=90)
    async with SessionLocal() as session:
        # delete old delivery attempts and events; in real prod use partitions
        await session.execute(delete(models.DeliveryAttempt).where(models.DeliveryAttempt.created_at < cutoff))
        await session.execute(delete(models.Outbox).where(models.Outbox.created_at < cutoff))
        await session.execute(delete(models.Event).where(models.Event.created < cutoff))
        await session.execute(delete(models.RawEvent).where(models.RawEvent.created_at < cutoff))
        await session.commit()


async def main():
    await run_retention()


if __name__ == "__main__":
    asyncio.run(main())

