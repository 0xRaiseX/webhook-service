from typing import List
from pydantic import BaseModel


class RawLog(BaseModel):
    chain_id: str
    block_number: int
    block_hash: str
    tx_hash: str
    tx_index: int
    log_index: int
    contract_address: str
    topics: List[str]
    data: str

