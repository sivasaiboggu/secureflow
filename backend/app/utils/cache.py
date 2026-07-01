import redis
import json
import logging
from typing import Any, Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)

class RedisCache:
    """Utility wrapper interfacing with Redis database caching and configuration maps"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.url = redis_url or settings.REDIS_URL
        try:
            self.client = redis.Redis.from_url(self.url, decode_responses=True)
        except Exception as e:
            logger.error(f"Failed connecting to Redis Cache at {self.url}: {e}")
            self.client = None

    def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        if not self.client:
            return False
        try:
            serialized = json.dumps(value)
            self.client.set(key, serialized, ex=expire_seconds)
            return True
        except Exception as e:
            logger.error(f"Redis cache write error for key {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Redis cache read error for key {key}: {e}")
        return None

    def delete(self, key: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis cache delete error for key {key}: {e}")
            return False

cache = RedisCache()
