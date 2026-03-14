"""Display formatting using Rich."""

from typing import List, Optional

from rich.console import Console
from rich.table import Table

from backends.base import PackageInfo


def display_search_results(packages: List[PackageInfo], show_numbers: bool = False, elapsed_ms: Optional[int] = None) -> List[PackageInfo]:
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
    table.add_column("Version", style="green", no_wrap=True)
    table.add_column("Source", style="blue", no_wrap=True)
    table.add_column("Description", style="dim")
    
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
        # Format version with installed status
        if pkg.is_installed:
            if pkg.installed_version and pkg.installed_version != pkg.version:
                version_display = f"{pkg.version} [magenta]({pkg.installed_version} ✓)[/magenta]"
            else:
                version_display = f"[magenta]{pkg.version} ✓[/magenta]"
        else:
            version_display = pkg.version
        
        row_args = []
        if show_numbers:
            row_args.append(str(i + 1))
        
        desc = pkg.description or ""
        desc_formatted = f"[dim white]{desc}[/dim white]" if i % 2 == 0 else f"[dim cyan]{desc}[/dim cyan]"
        
        row_args.extend([
            pkg.name,
            version_display,
            pkg.source,
            desc_formatted if desc else ""
        ])
        table.add_row(*row_args)
    
    console.print(table)
    footer_text = f"Found {len(packages)} package(s)"
    if elapsed_ms is not None:
        footer_text += f" (completed in {elapsed_ms} ms)"
    console.print(f"\n[dim]{footer_text}[/dim]")
    return sorted_packages
