import asyncio
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from ..store import models
from .evm_rpc import EvmRpcClient
from ..normalize.types import RawLog


class Scanner:
    def __init__(
        self,
        session: AsyncSession,
        rpc: EvmRpcClient,
        chain_id: str,
        confirmations: int = 12,
        batch_size: int = 1000,
    ):
        self.session = session
        self.rpc = rpc
        self.chain_id = chain_id
        self.confirmations = confirmations
        self.batch_size = batch_size

    async def load_state(self) -> models.ChainState:
        res = await self.session.execute(select(models.ChainState).where(models.ChainState.chain_id == self.chain_id))
        state = res.scalar_one_or_none()
        if state is None:
            state = models.ChainState(
                chain_id=self.chain_id,
                last_scanned_block=0,
                last_finalized_block=0,
                updated_at=datetime.utcnow(),
            )
            self.session.add(state)
            await self.session.commit()
        return state

    async def save_state(
        self, state: models.ChainState, last_block: int, finalized: int, last_block_hash: str | None = None
    ):
        await self.session.execute(
            update(models.ChainState)
            .where(models.ChainState.chain_id == self.chain_id)
            .values(
                last_scanned_block=last_block,
                last_finalized_block=finalized,
                last_block_hash=last_block_hash or state.last_block_hash,
                updated_at=datetime.utcnow(),
            )
        )
        await self.session.commit()

    async def run_once(self):
        state = await self.load_state()
        head = await self.rpc.get_block_number()
        finalized_head = head - self.confirmations

        # reorg detection: verify last scanned block hash if available
        if state.last_scanned_block > 0 and state.last_block_hash:
            blk = await self.rpc.get_block_by_number(state.last_scanned_block)
            current_hash = blk["hash"]
            if current_hash.lower() != state.last_block_hash.lower():
                # reorg detected, rewind
                rewind_to = max(state.last_scanned_block - self.confirmations, 0)
                await self.save_state(state, rewind_to, min(rewind_to, finalized_head))
                return 0

        start_block = state.last_scanned_block + 1
        to_block = min(finalized_head, start_block + self.batch_size - 1)
        if to_block < start_block:
            return 0

        logs = await self.rpc.get_logs(start_block, to_block)
        for log in logs:
            raw = RawLog(
                chain_id=self.chain_id,
                block_number=int(log["blockNumber"], 16),
                block_hash=log["blockHash"],
                tx_hash=log["transactionHash"],
                tx_index=int(log["transactionIndex"], 16),
                log_index=int(log["logIndex"], 16),
                contract_address=log["address"],
                topics=log["topics"],
                data=log["data"],
            )
            await self.session.execute(
                insert(models.RawEvent)
                .values(
                    id=f"{raw.tx_hash}:{raw.log_index}",
                    chain_id=raw.chain_id,
                    block_number=raw.block_number,
                    block_hash=raw.block_hash,
                    tx_hash=raw.tx_hash,
                    tx_index=raw.tx_index,
                    log_index=raw.log_index,
                    contract_address=raw.contract_address,
                    topics=raw.topics,
                    data=raw.data,
                )
                .prefix_with("ON CONFLICT DO NOTHING")
            )
        await self.session.commit()
        # record hash of last scanned block
        last_block = await self.rpc.get_block_by_number(to_block)
        await self.save_state(state, to_block, finalized_head, last_block_hash=last_block["hash"])
        return len(logs)

    async def loop(self, interval_sec: int = 5):
        while True:
            try:
                count = await self.run_once()
                await asyncio.sleep(interval_sec if count == 0 else 0)
            except Exception:
                await asyncio.sleep(interval_sec)

