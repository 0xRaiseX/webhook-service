from src.webhook_service.api.ratelimit import RateLimiter
import pytest


def test_rate_limiter_allows_then_blocks():
    limiter = RateLimiter(rate_per_min=2)
    limiter.check("proj")
    limiter.check("proj")
    with pytest.raises(Exception):
        limiter.check("proj")
