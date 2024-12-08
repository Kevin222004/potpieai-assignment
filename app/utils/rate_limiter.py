from fastapi import HTTPException, Request
from redis import Redis
from app.config import settings
import time


class RateLimiter:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.rate_limit = 10  # requests
        self.per_seconds = 60  # per minute

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"

        current = self.redis.get(key)
        if current is None:
            # First request, set to 1
            self.redis.setex(key, self.per_seconds, 1)
            return True

        current = int(current)
        if current >= self.rate_limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        self.redis.incr(key)
        return True