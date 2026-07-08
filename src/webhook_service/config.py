from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+asyncpg://webhook:webhook@localhost:5432/webhook",
        alias="DATABASE_URL",
    )
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    webhook_signature_tolerance_sec: int = Field(default=300, alias="WEBHOOK_SIG_TOLERANCE")
    default_confirmations: int = Field(default=12, alias="DEFAULT_CONFIRMATIONS")
    retry_schedule_seconds: List[int] = Field(
        default_factory=lambda: [60, 300, 900, 3600, 21600], alias="RETRY_SCHEDULE"
    )
    rpc_endpoints: List[str] = Field(
        default_factory=lambda: ["https://mainnet.infura.io/v3/demo"], alias="RPC_ENDPOINTS"
    )
    encryption_key: str = Field(
        default="insecure-demo-key-please-change", alias="ENCRYPTION_KEY"
    )
    api_rate_limit_per_min: int = Field(default=600, alias="API_RATE_LIMIT_PER_MIN")
    delivery_max_concurrency_per_endpoint: int = Field(
        default=5, alias="DELIVERY_MAX_CONCURRENCY_PER_ENDPOINT"
    )
    delivery_max_age_seconds: int = Field(default=86400, alias="DELIVERY_MAX_AGE_SECONDS")
    cors_origins: Optional[List[str]] = Field(default=None, alias="CORS_ORIGINS")

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]

