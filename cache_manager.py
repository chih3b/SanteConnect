"""
Simple in-memory cache for AI responses to speed up repeated queries
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class ResponseCache:
    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize cache with time-to-live
        
        Args:
            ttl_minutes: How long to keep cached responses (default 60 minutes)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def _get_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached response if exists and not expired"""
        key = self._get_key(query)
        
        if key in self.cache:
            cached = self.cache[key]
            if datetime.now() - cached['timestamp'] < self.ttl:
                print(f"✅ Cache hit for: {query[:50]}...")
                return cached['response']
            else:
                # Expired, remove it
                del self.cache[key]
        
        return None
    
    def set(self, query: str, response: Dict[str, Any]):
        """Cache a response"""
        key = self._get_key(query)
        self.cache[key] = {
            'response': response,
            'timestamp': datetime.now()
        }
        print(f"💾 Cached response for: {query[:50]}...")
    
    def clear(self):
        """Clear all cached responses"""
        self.cache.clear()
        print("🗑️ Cache cleared")
    
    def stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'total_entries': len(self.cache),
            'size_bytes': len(json.dumps(self.cache))
        }

# Global cache instance
_cache = ResponseCache(ttl_minutes=30)

def get_cache() -> ResponseCache:
    """Get the global cache instance"""
    return _cache
