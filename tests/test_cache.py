"""Tests for the search cache module."""

import time
import pytest
from pathlib import Path

from upk.cache import SearchCache, get_cache, CACHE_FILE
from upk.backends.base import PackageInfo


@pytest.fixture
def cache(tmp_path, monkeypatch):
    """Create a cache instance with a temporary cache file."""
    test_cache_file = tmp_path / "search_cache.json"
    monkeypatch.setattr("upk.cache.CACHE_FILE", test_cache_file)
    monkeypatch.setattr("upk.cache._cache_instance", None)
    return SearchCache(ttl_seconds=3600)


@pytest.fixture
def sample_packages():
    """Create sample PackageInfo objects for testing."""
    return [
        PackageInfo(
            name="firefox",
            version="131.0",
            source="apt",
            description="Web browser",
            installed_version="131.0",
            provides=[]
        ),
        PackageInfo(
            name="firefox",
            version="156.0",
            source="snap",
            description="Mozilla Firefox",
            installed_version=None,
            provides=[]
        ),
    ]


class TestSearchCache:
    """Tests for SearchCache class."""

    def test_set_and_get(self, cache, sample_packages):
        """Test storing and retrieving cached results."""
        cache.set("apt", "firefox", sample_packages[:1])
        
        result = cache.get("apt", "firefox")
        
        assert result is not None
        assert len(result) == 1
        assert result[0].name == "firefox"
        assert result[0].version == "131.0"
        assert result[0].source == "apt"

    def test_cache_miss(self, cache):
        """Test that missing entries return None."""
        result = cache.get("apt", "nonexistent")
        assert result is None

    def test_cache_expiration(self, tmp_path, monkeypatch, sample_packages):
        """Test that expired entries are not returned."""
        test_cache_file = tmp_path / "search_cache.json"
        monkeypatch.setattr("upk.cache.CACHE_FILE", test_cache_file)
        monkeypatch.setattr("upk.cache._cache_instance", None)
        
        # Create cache with 1 second TTL
        cache = SearchCache(ttl_seconds=1)
        cache.set("apt", "firefox", sample_packages[:1])
        
        # Should be available immediately
        assert cache.get("apt", "firefox") is not None
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired now
        assert cache.get("apt", "firefox") is None

    def test_invalidate(self, cache, sample_packages):
        """Test that invalidate clears all entries."""
        cache.set("apt", "firefox", sample_packages[:1])
        cache.set("snap", "firefox", sample_packages[1:])
        
        # Both should be cached
        assert cache.get("apt", "firefox") is not None
        assert cache.get("snap", "firefox") is not None
        
        # Invalidate
        cache.invalidate()
        
        # Both should be gone
        assert cache.get("apt", "firefox") is None
        assert cache.get("snap", "firefox") is None

    def test_different_backends_separate_keys(self, cache, sample_packages):
        """Test that different backends have separate cache entries."""
        cache.set("apt", "firefox", sample_packages[:1])
        cache.set("snap", "firefox", sample_packages[1:])
        
        apt_result = cache.get("apt", "firefox")
        snap_result = cache.get("snap", "firefox")
        
        assert apt_result[0].source == "apt"
        assert snap_result[0].source == "snap"

    def test_different_queries_separate_keys(self, cache, sample_packages):
        """Test that different queries have separate cache entries."""
        cache.set("apt", "firefox", sample_packages[:1])
        cache.set("apt", "chrome", [])
        
        firefox_result = cache.get("apt", "firefox")
        chrome_result = cache.get("apt", "chrome")
        
        assert firefox_result is not None
        assert chrome_result is not None
        assert len(firefox_result) == 1
        assert len(chrome_result) == 0

    def test_persistence(self, tmp_path, monkeypatch, sample_packages):
        """Test that cache persists across instances."""
        test_cache_file = tmp_path / "search_cache.json"
        monkeypatch.setattr("upk.cache.CACHE_FILE", test_cache_file)
        monkeypatch.setattr("upk.cache._cache_instance", None)
        
        # Create first instance and set data
        cache1 = SearchCache(ttl_seconds=3600)
        cache1.set("apt", "firefox", sample_packages[:1])
        
        # Create second instance (should load from disk)
        monkeypatch.setattr("upk.cache._cache_instance", None)
        cache2 = SearchCache(ttl_seconds=3600)
        result = cache2.get("apt", "firefox")
        
        assert result is not None
        assert result[0].name == "firefox"

    def test_corrupted_cache_file(self, tmp_path, monkeypatch):
        """Test that corrupted cache file is handled gracefully."""
        test_cache_file = tmp_path / "search_cache.json"
        monkeypatch.setattr("upk.cache.CACHE_FILE", test_cache_file)
        monkeypatch.setattr("upk.cache._cache_instance", None)
        
        # Write invalid JSON
        test_cache_file.write_text("not valid json{{{")
        
        # Should not raise, should start with empty cache
        cache = SearchCache(ttl_seconds=3600)
        assert cache.get("apt", "firefox") is None

    def test_package_serialization(self, cache, sample_packages):
        """Test that PackageInfo objects are correctly serialized/deserialized."""
        pkg = PackageInfo(
            name="test-pkg",
            version="1.0.0",
            source="test",
            description="Test description",
            installed_version="1.0.0",
            provides=["virtual-pkg"]
        )
        
        cache.set("test", "query", [pkg])
        result = cache.get("test", "query")
        
        assert result is not None
        assert len(result) == 1
        
        cached_pkg = result[0]
        assert cached_pkg.name == pkg.name
        assert cached_pkg.version == pkg.version
        assert cached_pkg.source == pkg.source
        assert cached_pkg.description == pkg.description
        assert cached_pkg.installed_version == pkg.installed_version
        assert cached_pkg.provides == pkg.provides


class TestGetCache:
    """Tests for the get_cache() singleton function."""

    def test_get_cache_returns_instance(self, monkeypatch, tmp_path):
        """Test that get_cache() returns a SearchCache instance."""
        test_cache_file = tmp_path / "search_cache.json"
        monkeypatch.setattr("upk.cache.CACHE_FILE", test_cache_file)
        monkeypatch.setattr("upk.cache._cache_instance", None)
        
        cache = get_cache()
        assert isinstance(cache, SearchCache)

    def test_get_cache_returns_same_instance(self, monkeypatch, tmp_path):
        """Test that get_cache() returns the same instance on multiple calls."""
        test_cache_file = tmp_path / "search_cache.json"
        monkeypatch.setattr("upk.cache.CACHE_FILE", test_cache_file)
        monkeypatch.setattr("upk.cache._cache_instance", None)
        
        cache1 = get_cache()
        cache2 = get_cache()
        
        assert cache1 is cache2
