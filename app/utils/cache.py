from redis import Redis
import json
from app.config import settings
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.default_ttl = 3600  # Cache for 1 hour

    async def get(self, key: str) -> Optional[Any]:
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        try:
            return self.redis.setex(
                key,
                ttl or self.default_ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    def get_pr_cache_key(self, repo_url: str, pr_number: int) -> str:
        return f"pr_analysis:{repo_url}:{pr_number}"