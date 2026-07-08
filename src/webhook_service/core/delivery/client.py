import httpx
import asyncio
from typing import Any, Dict
from collections import defaultdict


class WebhookClient:
    def __init__(self, timeout: float = 5.0, max_concurrency_per_endpoint: int = 5):
        self.client = httpx.AsyncClient(timeout=timeout)
        self.max_concurrency_per_endpoint = max_concurrency_per_endpoint
        self._locks = defaultdict(lambda: asyncio.Semaphore(self.max_concurrency_per_endpoint))

    async def post(
        self, url: str, payload: Dict[str, Any], headers: Dict[str, str], endpoint_id: str
    ) -> httpx.Response:
        sem = self._locks[endpoint_id]
        async with sem:
            return await self.client.post(url, json=payload, headers=headers)

    async def close(self):
        await self.client.aclose()

