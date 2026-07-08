from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SubscriptionFilters(BaseModel):
    chain_id: Optional[List[str]] = None
    contract_address: Optional[List[str]] = None
    topic0: Optional[List[str]] = None
    from_address: Optional[List[str]] = None
    to_address: Optional[List[str]] = None
    token_address: Optional[List[str]] = None
    token_id: Optional[List[str]] = None
    abi_event: Optional[str] = None
    args: Optional[Dict[str, Any]] = None


class Subscription(BaseModel):
    id: str
    project_id: str
    endpoint_id: str
    event_types: List[str]
    filters: SubscriptionFilters
    confirmations: int
    status: str

