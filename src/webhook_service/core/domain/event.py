from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class EventSource(BaseModel):
    chain_id: str
    network: Optional[str] = None
    block_number: int
    block_hash: str
    tx_hash: str
    tx_index: int
    log_index: int
    contract_address: str


class EventData(BaseModel):
    normalized: Dict[str, Any]
    raw: Optional[Dict[str, Any]] = None


class CanonicalEvent(BaseModel):
    id: str
    type: str
    created: int = Field(description="unix timestamp")
    project_id: str
    api_version: str
    source: EventSource
    data: EventData
    links: Optional[Dict[str, Any]] = None

    @property
    def created_dt(self) -> datetime:
        return datetime.utcfromtimestamp(self.created)

