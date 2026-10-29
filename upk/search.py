"""Search coordinator for aggregating results from multiple backends."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Optional

from .backends.base import Backend, PackageInfo
from .cache import get_cache


def _search_single_backend(
    backend: Backend,
    query: str,
    use_cache: bool = True
) -> List[PackageInfo]:
    """
    Search a single backend with optional caching.

    Args:
        backend: Backend instance to search
        query: Search term
        use_cache: Whether to read from cache (always writes if cache available)

    Returns:
        List of PackageInfo from the backend
    """
    cache = get_cache()

    # Try cache first (unless bypassing)
    if use_cache and cache is not None:
        cached = cache.get(backend.name, query)
        if cached is not None:
            return cached

    # Cache miss or bypassed — call the backend
    results = backend.search(query)

    # Always update cache with fresh results
    if cache is not None:
        cache.set(backend.name, query, results)

    return results


def search_all_backends(
    backends: List[Backend], 
    query: str,
    progress_callback: Optional[Callable[[str, bool], None]] = None,
    use_cache: bool = True
) -> List[PackageInfo]:
    """
    Search across all backends in parallel.
    
    Args:
        backends: List of backend instances to search
        query: Search term
        progress_callback: Optional callback function(backend_name, completed)
        use_cache: Whether to use search cache
        
    Returns:
        Aggregated list of PackageInfo from all backends
    """
    all_results = []
    
    # Execute searches in parallel
    with ThreadPoolExecutor(max_workers=len(backends)) as executor:
        # Submit all search tasks
        future_to_backend = {
            executor.submit(_search_single_backend, backend, query, use_cache): backend
            for backend in backends
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_backend):
            backend = future_to_backend[future]
            try:
                results = future.result(timeout=15)
                all_results.extend(results)
                if progress_callback:
                    progress_callback(backend.name, True)
            except Exception as e:
                # Log error but continue with other backends
                if progress_callback:
                    progress_callback(backend.name, False)
                print(f"Warning: Search failed for {backend.name}: {e}")
    
    return all_results

def list_all_backends(
    backends: List[Backend], 
    progress_callback: Optional[Callable[[str, bool], None]] = None
) -> List[PackageInfo]:
    """
    List installed packages across all backends in parallel.
    
    Args:
        backends: List of backend instances to search
        progress_callback: Optional callback function(backend_name, completed)
        
    Returns:
        Aggregated list of installed PackageInfo from all backends
    """
    all_results = []
    
    # Execute listing in parallel
    with ThreadPoolExecutor(max_workers=len(backends)) as executor:
        # Submit all listing tasks
        future_to_backend = {
            executor.submit(backend.list_packages): backend
            for backend in backends
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_backend):
            backend = future_to_backend[future]
            try:
                results = future.result(timeout=15)
                all_results.extend(results)
                if progress_callback:
                    progress_callback(backend.name, True)
            except Exception as e:
                # Log error but continue with other backends
                if progress_callback:
                    progress_callback(backend.name, False)
                print(f"Warning: Listing failed for {backend.name}: {e}")
    
    return all_results
