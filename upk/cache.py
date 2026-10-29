"""Search result cache for UPK."""

import json
import threading
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from .backends.base import PackageInfo


CACHE_DIR = Path.home() / ".cache" / "upk"
CACHE_FILE = CACHE_DIR / "search_cache.json"
DEFAULT_TTL_SECONDS = 86400  # 1 day


class SearchCache:
    """Cache for search results with TTL-based expiration."""

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load cache from disk."""
        if not CACHE_FILE.exists():
            self._cache = {}
            return

        try:
            with open(CACHE_FILE, 'r') as f:
                self._cache = json.load(f)
        except Exception:
            # Corrupted cache file, start fresh
            self._cache = {}

    def _save(self) -> None:
        """Save cache to disk (must be called with lock held)."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            # Write to temp file first, then rename for atomicity
            temp_file = CACHE_FILE.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
            temp_file.replace(CACHE_FILE)
        except Exception:
            # Silently fail on write errors
            pass

    def _make_key(self, backend_name: str, query: str) -> str:
        """Create cache key from backend name and query."""
        return f"{backend_name}:{query}"

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if a cache entry has expired."""
        timestamp = entry.get('timestamp', 0)
        return (time.time() - timestamp) > self.ttl_seconds

    def _package_to_dict(self, pkg: PackageInfo) -> Dict[str, Any]:
        """Serialize PackageInfo to dict."""
        return {
            'name': pkg.name,
            'version': pkg.version,
            'source': pkg.source,
            'description': pkg.description,
            'installed_version': pkg.installed_version,
            'provides': pkg.provides or []
        }

    def _dict_to_package(self, data: Dict[str, Any]) -> PackageInfo:
        """Deserialize dict to PackageInfo."""
        return PackageInfo(
            name=data['name'],
            version=data['version'],
            source=data['source'],
            description=data.get('description'),
            installed_version=data.get('installed_version'),
            provides=data.get('provides', [])
        )

    def get(self, backend_name: str, query: str) -> Optional[List[PackageInfo]]:
        """
        Get cached search results if available and not expired.

        Args:
            backend_name: Name of the backend
            query: Search query

        Returns:
            List of PackageInfo if cache hit, None if cache miss or expired
        """
        key = self._make_key(backend_name, query)

        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if self._is_expired(entry):
                # Remove expired entry
                del self._cache[key]
                self._save()
                return None

            # Cache hit
            try:
                results = [self._dict_to_package(d) for d in entry['results']]
                return results
            except Exception:
                # Corrupted entry, remove it
                del self._cache[key]
                self._save()
                return None

    def set(self, backend_name: str, query: str, results: List[PackageInfo]) -> None:
        """
        Store search results in cache.

        Args:
            backend_name: Name of the backend
            query: Search query
            results: List of PackageInfo to cache
        """
        key = self._make_key(backend_name, query)

        with self._lock:
            self._cache[key] = {
                'timestamp': time.time(),
                'results': [self._package_to_dict(pkg) for pkg in results]
            }
            self._save()

    def invalidate(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache = {}
            self._save()


# Global cache instance
_cache_instance: Optional[SearchCache] = None
_cache_lock = threading.Lock()


def get_cache() -> SearchCache:
    """Get the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = SearchCache()
    return _cache_instance
