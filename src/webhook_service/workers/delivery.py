import asyncio
from ..config import get_settings
from ..db import SessionLocal
from ..core.delivery.worker import DeliveryWorker


async def main():
    settings = get_settings()
    worker = DeliveryWorker(SessionLocal, settings)
    await worker.loop()


if __name__ == "__main__":
    asyncio.run(main())

