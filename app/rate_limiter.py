"""Rate limiting & API key auth for FastAPI.

Per-key quotas: defaults to 1000 calls/month, upgrade tiers available.
Simple in-memory rate limiter for single-instance; use Redis for distributed.
"""
import time
from typing import Optional
from fastapi import Header, HTTPException, status

# In-memory store: {api_key: {count, reset_at}}
# For production, use Redis: redis.setex(f"quota:{api_key}", 2592000, count)
quota_store = {}

TIER_LIMITS = {
    "free": 100,      # 100 calls/month
    "pro": 1000,      # 1000 calls/month
    "enterprise": 100000,  # Unlimited (soft cap)
}


def get_api_key_tier(api_key: str) -> str:
    """Look up tier from a DB or config. Stub: return 'free'."""
    # In production: query api_keys table for tier
    return "free"


async def rate_limit(x_api_key: Optional[str] = Header(None)) -> str:
    """Validate API key and check rate limit. Return the key if valid."""
    if not x_api_key:
        # No key = mock mode, unlimited but logged
        return "anonymous"

    tier = get_api_key_tier(x_api_key)
    limit = TIER_LIMITS.get(tier, 100)
    reset_at = time.time() + 2592000  # 30 days

    if x_api_key not in quota_store:
        quota_store[x_api_key] = {"count": 0, "reset_at": reset_at}

    entry = quota_store[x_api_key]

    # Reset if 30 days have passed
    if time.time() > entry["reset_at"]:
        entry["count"] = 0
        entry["reset_at"] = reset_at

    # Check limit
    if entry["count"] >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {entry['count']}/{limit} calls used this month.",
        )

    entry["count"] += 1
    return x_api_key
