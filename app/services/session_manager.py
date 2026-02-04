"""
Session Manager with Upstash Redis and Local File Store Fallback.
Handles session persistence with automatic TTL and graceful degradation.
"""
import logging
import time
from typing import Optional
from functools import lru_cache
from collections import OrderedDict
import httpx
import orjson

from app.config import get_settings
from app.schemas.session import SessionData
from app.services.local_store import LocalFileStore

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple LRU cache for fallback when Redis is unavailable."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, bytes] = OrderedDict()
    
    def get(self, key: str) -> Optional[bytes]:
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
        return None
    
    def set(self, key: str, value: bytes) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        # Evict oldest if over capacity
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False


class SessionManager:
    """
    Manages session state with Upstash Redis REST API.
    Falls back to LocalFileStore if Redis is unavailable.
    
    Key Schema: honeypot:session:{sessionId}
    TTL: 1 hour (3600 seconds)
    """
    
    def __init__(self):
        settings = get_settings()
        self.redis_url = settings.UPSTASH_REDIS_REST_URL
        self.redis_token = settings.UPSTASH_REDIS_REST_TOKEN
        self.ttl = settings.SESSION_TTL_SECONDS
        self.key_prefix = settings.SESSION_KEY_PREFIX
        
        # Fallback to persistent local file store
        self._fallback_store = LocalFileStore()
        self._using_fallback = False
        self._last_redis_failure = 0.0
        self._redis_retry_seconds = 30
        
        # HTTP client for Upstash REST API
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for Upstash."""
        if not self.redis_url or not self.redis_token:
            raise RuntimeError("Upstash configuration missing")
        if self._client is None or getattr(self._client, "is_closed", False):
            self._client = httpx.AsyncClient(
                base_url=self.redis_url,
                headers={"Authorization": f"Bearer {self.redis_token}"},
                timeout=5.0,
            )
        return self._client
    
    def _make_key(self, session_id: str) -> str:
        """Create Redis key from session ID."""
        return f"{self.key_prefix}{session_id}"
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Retrieve session data from Redis or fallback cache.
        
        Returns None if session doesn't exist.
        """
        key = self._make_key(session_id)
        
        # Try Redis first
        if self._using_fallback:
            if (time.monotonic() - self._last_redis_failure) >= self._redis_retry_seconds:
                self._using_fallback = False
        if not self._using_fallback:
            try:
                client = await self._get_client()
                response = await client.get(f"/get/{key}")
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result")
                    if result:
                        session_dict = orjson.loads(result)
                        return SessionData(**session_dict)
                    return None
                else:
                    logger.warning(f"Redis GET failed with status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Redis connection failed, switching to fallback: {e}")
                self._using_fallback = True
                self._last_redis_failure = time.monotonic()
        
        # Fallback to local file store
        cached = self._fallback_store.get(session_id)
        if cached:
            return SessionData(**cached)
        
        return None
    
    async def save_session(self, session_id: str, data: SessionData) -> bool:
        """
        Save session data to Redis with TTL, or to fallback cache.
        
        Returns True on success.
        """
        key = self._make_key(session_id)
        json_data = orjson.dumps(data.model_dump()).decode("utf-8")
        
        # Try Redis first
        if self._using_fallback:
            if (time.monotonic() - self._last_redis_failure) >= self._redis_retry_seconds:
                self._using_fallback = False
        if not self._using_fallback:
            try:
                client = await self._get_client()
                # SETEX key ttl value
                response = await client.post(
                    f"/setex/{key}/{self.ttl}",
                    content=json_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.warning(f"Redis SETEX failed with status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Redis save failed, using fallback: {e}")
                self._using_fallback = True
                self._last_redis_failure = time.monotonic()
        
        # Fallback to local file store
        self._fallback_store.set(session_id, data.model_dump(), ttl_seconds=self.ttl)
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session from Redis or fallback cache."""
        key = self._make_key(session_id)
        
        if not self._using_fallback:
            try:
                client = await self._get_client()
                response = await client.get(f"/del/{key}")
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Redis delete failed: {e}")
                self._using_fallback = True
                self._last_redis_failure = time.monotonic()
        
        return self._fallback_store.delete(session_id)
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def is_using_fallback(self) -> bool:
        """Check if currently using fallback cache."""
        return self._using_fallback
    
    async def reset_fallback_mode(self) -> None:
        """Attempt to reconnect to Redis."""
        self._using_fallback = False


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the singleton SessionManager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
