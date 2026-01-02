"""
🐦 BirdSense - Bird Enrichment Cache
Developed by Soham

Provides caching for bird enrichment data to speed up repeated lookups.
TTL-based cache with background refresh capability.
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import hashlib


class BirdEnrichmentCache:
    """
    Thread-safe cache for bird enrichment data.
    
    Features:
    - TTL-based expiration (default 24 hours)
    - Background refresh for expired entries
    - Statistics tracking
    - Preserves full enrichment data including images
    """
    
    def __init__(self, ttl_hours: int = 24, max_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._ttl = timedelta(hours=ttl_hours)
        self._max_size = max_size
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=3)
        
        # Stats
        self._hits = 0
        self._misses = 0
        self._background_refreshes = 0
    
    def _make_key(self, bird_name: str, location: str = "") -> str:
        """Create normalized cache key."""
        normalized = f"{bird_name.lower().strip()}|{location.lower().strip()}"
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def get(self, bird_name: str, location: str = "") -> Optional[Dict[str, Any]]:
        """
        Get cached enrichment data.
        Returns None if not cached or expired.
        """
        key = self._make_key(bird_name, location)
        
        with self._lock:
            if key in self._cache:
                timestamp = self._timestamps.get(key)
                if timestamp and datetime.now() - timestamp < self._ttl:
                    self._hits += 1
                    return self._cache[key].copy()
                else:
                    # Expired - remove
                    del self._cache[key]
                    if key in self._timestamps:
                        del self._timestamps[key]
            
            self._misses += 1
            return None
    
    def set(self, bird_name: str, data: Dict[str, Any], location: str = ""):
        """Cache enrichment data."""
        key = self._make_key(bird_name, location)
        
        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._timestamps, key=lambda k: self._timestamps[k])
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]
            
            self._cache[key] = data.copy()
            self._timestamps[key] = datetime.now()
    
    def get_or_fetch(
        self, 
        bird_name: str, 
        fetch_func: Callable[[], Dict[str, Any]],
        location: str = ""
    ) -> Dict[str, Any]:
        """
        Get from cache or fetch using provided function.
        This is the main entry point for cached enrichment.
        """
        cached = self.get(bird_name, location)
        if cached:
            print(f"🚀 Cache HIT: {bird_name}")
            return cached
        
        print(f"📥 Cache MISS: {bird_name} - fetching...")
        start = time.time()
        data = fetch_func()
        duration = int((time.time() - start) * 1000)
        print(f"✅ Cached: {bird_name} ({duration}ms)")
        
        self.set(bird_name, data, location)
        return data
    
    def refresh_async(
        self, 
        bird_name: str, 
        fetch_func: Callable[[], Dict[str, Any]],
        location: str = ""
    ):
        """Schedule background refresh for a bird."""
        def _refresh():
            try:
                print(f"🔄 Background refresh: {bird_name}")
                data = fetch_func()
                self.set(bird_name, data, location)
                with self._lock:
                    self._background_refreshes += 1
                print(f"✅ Background refresh complete: {bird_name}")
            except Exception as e:
                print(f"⚠️ Background refresh failed for {bird_name}: {e}")
        
        self._executor.submit(_refresh)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "total_cached": len(self._cache),
                "max_size": self._max_size,
                "ttl_hours": int(self._ttl.total_seconds() / 3600),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 1),
                "background_refreshes": self._background_refreshes
            }
    
    def clear(self):
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0


# Global cache instance
bird_cache = BirdEnrichmentCache(ttl_hours=24, max_size=1000)


def get_cached_enrichment(
    bird_name: str,
    scientific_name: str = "",
    location: str = "",
    enrichment_func: Callable = None
) -> Dict[str, Any]:
    """
    Get bird enrichment with caching.
    
    This wraps the original get_enriched_bird_info function with caching.
    Falls back to direct call if no cache available.
    """
    if enrichment_func is None:
        # Import here to avoid circular import
        from analysis import get_enriched_bird_info
        enrichment_func = lambda: get_enriched_bird_info(bird_name, scientific_name, location)
    
    return bird_cache.get_or_fetch(
        bird_name=bird_name,
        fetch_func=enrichment_func,
        location=location
    )


def schedule_background_enrichment(
    bird_name: str,
    scientific_name: str = "",
    location: str = ""
):
    """
    Schedule background enrichment for a bird.
    Useful for pre-caching or refreshing stale data.
    """
    from analysis import get_enriched_bird_info
    
    bird_cache.refresh_async(
        bird_name=bird_name,
        fetch_func=lambda: get_enriched_bird_info(bird_name, scientific_name, location),
        location=location
    )

