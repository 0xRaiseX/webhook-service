import asyncio
from ..config import get_settings
from ..db import SessionLocal
from ..core.ingest.evm_rpc import EvmRpcClient
from ..core.ingest.scanner import Scanner


async def main():
    settings = get_settings()
    rpc = EvmRpcClient(settings.rpc_endpoints)
    async with SessionLocal() as session:
        scanner = Scanner(session, rpc, chain_id="1", confirmations=settings.default_confirmations)
        await scanner.loop()


if __name__ == "__main__":
    asyncio.run(main())

