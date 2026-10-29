"""Tests for the search module."""

import pytest
from unittest.mock import Mock, patch

from upk.search import search_all_backends, _search_single_backend
from upk.backends.base import Backend, PackageInfo
from upk.cache import SearchCache


class MockBackend(Backend):
    """Mock backend for testing."""
    
    def __init__(self, name="mock", packages=None, search_delay=0):
        self._name = name
        self._packages = packages or []
        self._search_delay = search_delay
        self.search_call_count = 0
    
    @property
    def name(self):
        return self._name
    
    def is_available(self):
        return True
    
    def search(self, query):
        import time
        self.search_call_count += 1
        if self._search_delay > 0:
            time.sleep(self._search_delay)
        # Return packages that match the query
        return [p for p in self._packages if query.lower() in p.name.lower()]
    
    def get_installed_version(self, package_name):
        for p in self._packages:
            if p.name == package_name and p.installed_version:
                return p.installed_version
        return None
    
    def install(self, package_name, extra_args=None):
        return True
    
    def update(self):
        return True
    
    def upgrade(self, package_name=None, extra_args=None):
        return True
    
    def remove(self, package_name, extra_args=None):
        return True
    
    def list_packages(self):
        return [p for p in self._packages if p.installed_version]


@pytest.fixture
def mock_packages():
    """Create sample packages for testing."""
    return [
        PackageInfo(
            name="firefox",
            version="131.0",
            source="mock1",
            description="Web browser",
            installed_version=None
        ),
        PackageInfo(
            name="firefox-esr",
            version="128.0",
            source="mock1",
            description="Web browser (ESR)",
            installed_version="128.0"
        ),
        PackageInfo(
            name="chromium",
            version="120.0",
            source="mock1",
            description="Open source browser",
            installed_version=None
        ),
    ]


@pytest.fixture
def mock_backend(mock_packages):
    """Create a mock backend with sample packages."""
    return MockBackend(name="mock1", packages=mock_packages)


@pytest.fixture(autouse=True)
def clear_cache(monkeypatch, tmp_path):
    """Clear cache before each test."""
    test_cache_file = tmp_path / "search_cache.json"
    monkeypatch.setattr("upk.cache.CACHE_FILE", test_cache_file)
    monkeypatch.setattr("upk.cache._cache_instance", None)
    monkeypatch.setattr("upk.search.get_cache", lambda: SearchCache(ttl_seconds=3600))


class TestSearchSingleBackend:
    """Tests for _search_single_backend function."""
    
    def test_search_without_cache(self, mock_backend):
        """Test search without using cache."""
        results = _search_single_backend(mock_backend, "firefox", use_cache=False)
        
        assert len(results) == 2
        assert mock_backend.search_call_count == 1
    
    def test_search_with_cache_miss(self, mock_backend):
        """Test search with cache miss."""
        results = _search_single_backend(mock_backend, "firefox", use_cache=True)
        
        assert len(results) == 2
        assert mock_backend.search_call_count == 1
    
    def test_search_with_cache_hit(self, mock_backend):
        """Test search with cache hit."""
        # First search (cache miss)
        results1 = _search_single_backend(mock_backend, "firefox", use_cache=True)
        assert mock_backend.search_call_count == 1
        
        # Second search (cache hit)
        results2 = _search_single_backend(mock_backend, "firefox", use_cache=True)
        assert mock_backend.search_call_count == 1  # Not called again
        
        assert len(results1) == len(results2)
    
    def test_search_no_cache_bypasses_read_but_writes(self, mock_backend):
        """Test that use_cache=False bypasses read but still writes."""
        # First search with cache disabled
        results1 = _search_single_backend(mock_backend, "firefox", use_cache=False)
        assert mock_backend.search_call_count == 1
        
        # Second search with cache enabled should hit cache
        results2 = _search_single_backend(mock_backend, "firefox", use_cache=True)
        assert mock_backend.search_call_count == 1  # Not called again
        
        assert len(results1) == len(results2)


class TestSearchAllBackends:
    """Tests for search_all_backends function."""
    
    def test_search_multiple_backends(self, mock_packages):
        """Test searching across multiple backends."""
        backend1 = MockBackend(name="backend1", packages=mock_packages[:2])
        backend2 = MockBackend(name="backend2", packages=mock_packages[1:])
        
        results = search_all_backends([backend1, backend2], "firefox", use_cache=False)
        
        # Should get results from both backends
        assert len(results) == 3  # 2 from backend1 + 1 from backend2 (chromium doesn't match)
        assert backend1.search_call_count == 1
        assert backend2.search_call_count == 1
    
    def test_search_with_progress_callback(self, mock_backend):
        """Test that progress callback is called."""
        callback_calls = []
        
        def callback(backend_name, success):
            callback_calls.append((backend_name, success))
        
        search_all_backends([mock_backend], "firefox", callback, use_cache=False)
        
        assert len(callback_calls) == 1
        assert callback_calls[0] == ("mock1", True)
    
    def test_search_handles_backend_error(self):
        """Test that search continues when a backend fails."""
        failing_backend = MockBackend(name="failing")
        failing_backend.search = Mock(side_effect=Exception("Search failed"))
        
        working_backend = MockBackend(
            name="working",
            packages=[PackageInfo(name="test", version="1.0", source="working")]
        )
        
        results = search_all_backends(
            [failing_backend, working_backend],
            "test",
            use_cache=False
        )
        
        # Should get results from working backend
        assert len(results) == 1
        assert results[0].name == "test"
    
    def test_search_empty_results(self, mock_backend):
        """Test search with no matching results."""
        results = search_all_backends([mock_backend], "nonexistent", use_cache=False)
        assert len(results) == 0
    
    def test_search_caches_results(self, mock_backend):
        """Test that search results are cached."""
        # First search
        results1 = search_all_backends([mock_backend], "firefox", use_cache=True)
        assert mock_backend.search_call_count == 1
        
        # Second search should use cache
        results2 = search_all_backends([mock_backend], "firefox", use_cache=True)
        assert mock_backend.search_call_count == 1  # Not called again
        
        assert len(results1) == len(results2)
