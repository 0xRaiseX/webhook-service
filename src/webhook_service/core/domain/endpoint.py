from pydantic import BaseModel, HttpUrl
from typing import Optional


class Endpoint(BaseModel):
    id: str
    project_id: str
    url: HttpUrl
    status: str
    rate_limit_rps: Optional[int] = None

