import json
from typing import Optional, Dict, Any, Union
import redis
from datetime import timedelta
import os
from mlb_storyteller.config import CACHE_ENABLED, CACHE_TTL

class RedisService:
    """Redis caching service for MLB Storyteller."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.enabled = CACHE_ENABLED
        self.ttl = CACHE_TTL
        self.redis = redis.Redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379'),
            encoding='utf-8',
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached data by key."""
        if not self.enabled:
            return None
            
        data = self.redis.get(key)
        return json.loads(data) if data else None
    
    async def set(self, key: str, data: Any, expire: Optional[int] = None):
        """Set cached data with optional expiration."""
        if not self.enabled:
            return
            
        if expire:
            self.redis.setex(
                key,
                timedelta(seconds=expire),
                json.dumps(data)
            )
        else:
            self.redis.set(key, json.dumps(data))
        
    async def get_game_data(self, game_id: str) -> Optional[Dict]:
        """Get cached game data."""
        if not self.enabled:
            return None
            
        key = f"game:{game_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None
        
    async def set_game_data(self, game_id: str, data: Dict):
        """Cache game data."""
        if not self.enabled:
            return
            
        key = f"game:{game_id}"
        self.redis.setex(
            key,
            timedelta(seconds=self.ttl),
            json.dumps(data)
        )
        
    async def get_popular_stats(self, stat_type: str) -> Optional[Dict]:
        """Get cached popular statistics (teams/players)."""
        if not self.enabled:
            return None
            
        key = f"stats:{stat_type}"
        data = self.redis.get(key)
        return json.loads(data) if data else None
        
    async def set_popular_stats(self, stat_type: str, data: Dict):
        """Cache popular statistics."""
        if not self.enabled:
            return
            
        key = f"stats:{stat_type}"
        self.redis.setex(
            key,
            timedelta(hours=1),  # Stats cache for 1 hour
            json.dumps(data)
        )
        
    async def invalidate_game_cache(self, game_id: str):
        """Invalidate cached game data."""
        if not self.enabled:
            return
            
        key = f"game:{game_id}"
        self.redis.delete(key)
        
    async def invalidate_stats_cache(self):
        """Invalidate all stats caches."""
        if not self.enabled:
            return
            
        keys = self.redis.keys("stats:*")
        if keys:
            self.redis.delete(*keys)
            
    async def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            return self.redis.ping()
        except Exception:
            return False 