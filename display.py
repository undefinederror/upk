"""Display formatting using Rich."""

from typing import List

from rich.console import Console
from rich.table import Table

from backends.base import PackageInfo


def display_search_results(packages: List[PackageInfo], show_numbers: bool = False) -> List[PackageInfo]:
    """
    Display search results in a formatted table.
    
    Args:
        packages: List of PackageInfo objects to display
        show_numbers: Whether to display a number column for selection
        
    Returns:
        List of sorted PackageInfo objects
    """
    console = Console()
    
    if not packages:
        console.print("[yellow]No packages found.[/yellow]")
        return []
    
    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    if show_numbers:
        table.add_column("#", style="dim", justify="right")
    table.add_column("Package Name", style="white", no_wrap=True)
    table.add_column("Version", style="green")
    table.add_column("Source", style="blue")
    table.add_column("Installed", style="magenta")
    
    # Get sort order from config
    try:
        from config import load_config
        config = load_config()
        priority = config.get("backends_priority", [])
    except ImportError:
        priority = ["apt", "snap", "flatpak", "pacstall"]
        
    def get_sort_key(pkg):
        try:
            source_idx = priority.index(pkg.source.lower())
        except ValueError:
            source_idx = 999
        return (pkg.name.lower(), source_idx)
        
    # Sort packages by name, then by configured source priority
    sorted_packages = sorted(packages, key=get_sort_key)
    
    # Add rows
    for i, pkg in enumerate(sorted_packages):
        installed_status = ""
        if pkg.is_installed:
            installed_status = f"{pkg.installed_version} ✓"
        
        row_args = []
        if show_numbers:
            row_args.append(str(i + 1))
        row_args.extend([
            pkg.name,
            pkg.version,
            pkg.source,
            installed_status
        ])
        table.add_row(*row_args)
    
    console.print(table)
    console.print(f"\n[dim]Found {len(packages)} package(s)[/dim]")
    return sorted_packages
