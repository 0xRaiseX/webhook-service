import httpx
import asyncio
from typing import Any, List


class EvmRpcClient:
    def __init__(self, endpoints: List[str], timeout: float = 10.0):
        self.endpoints = endpoints
        self.timeout = timeout
        self._index = 0

    def _next_endpoint(self) -> str:
        endpoint = self.endpoints[self._index % len(self.endpoints)]
        self._index += 1
        return endpoint

    async def _post(self, payload: dict) -> Any:
        url = self._next_endpoint()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise RuntimeError(data["error"])
            return data["result"]

    async def get_block_number(self) -> int:
        result = await self._post({"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []})
        return int(result, 16)

    async def get_logs(self, from_block: int, to_block: int, addresses: List[str] | None = None, topics=None):
        params = {
            "fromBlock": hex(from_block),
            "toBlock": hex(to_block),
        }
        if addresses:
            params["address"] = addresses
        if topics:
            params["topics"] = topics
        result = await self._post({"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [params]})
        return result

    async def get_block_by_number(self, block_number: int) -> Any:
        result = await self._post(
            {"jsonrpc": "2.0", "id": 1, "method": "eth_getBlockByNumber", "params": [hex(block_number), False]}
        )
        return result

    async def batch(self, requests: List[dict]) -> List[Any]:
        url = self._next_endpoint()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=requests)
            resp.raise_for_status()
            raw = resp.json()
            # assumes order preserved
            return [item["result"] for item in sorted(raw, key=lambda x: x["id"])]

