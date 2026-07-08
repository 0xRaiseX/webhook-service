import time
from typing import Dict
from fastapi import HTTPException, status
from ..config import get_settings


class TokenBucket:
    def __init__(self, rate_per_min: int):
        self.rate = rate_per_min
        self.allowance = rate_per_min
        self.last_check = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        elapsed = now - self.last_check
        self.last_check = now
        self.allowance = min(self.rate, self.allowance + elapsed * (self.rate / 60.0))
        if self.allowance < tokens:
            return False
        self.allowance -= tokens
        return True


class RateLimiter:
    def __init__(self, rate_per_min: int):
        self.rate_per_min = rate_per_min
        self.buckets: Dict[str, TokenBucket] = {}

    def check(self, key: str):
        bucket = self.buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(self.rate_per_min)
            self.buckets[key] = bucket
        if not bucket.consume():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")


_limiter = RateLimiter(get_settings().api_rate_limit_per_min)


def rate_limit(project_id: str):
    _limiter.check(project_id)

