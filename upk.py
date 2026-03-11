#!/usr/bin/env python3
"""UPK - Ubuntu Package Kit: Universal package manager wrapper."""

import click

from backends import AptBackend, SnapBackend, FlatpakBackend, PacstallBackend, AppImageBackend
from display import display_search_results
from search import search_all_backends


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """UPK - Ubuntu Package Kit
    
    A unified interface for searching and managing packages across
    multiple package managers (APT, Snap, and more).
    """
    pass

def get_configured_backends(source: str = None) -> list:
    """Get initialized, available backends filtered by config and requested source."""
    backends = [
        AptBackend(),
        SnapBackend(),
        FlatpakBackend(),
        PacstallBackend(),
        AppImageBackend(),
    ]
    available = [b for b in backends if b.is_available()]
    
    if source:
        available = [b for b in available if b.name == source]
        return available
        
    try:
        from config import load_config
        config = load_config()
        disabled = config.get("disabled_backends", [])
        preference = config.get("backends_priority", ["apt", "flatpak", "snap", "pacstall"])
        
        # Filter disabled
        available = [b for b in available if b.name not in disabled]
        
        # Sort by preference
        def get_sort_key(b):
            try:
                return preference.index(b.name)
            except ValueError:
                return 999
                
        available = sorted(available, key=get_sort_key)
    except ImportError:
        pass
        
    return available


def get_backend_from_name(backend_name: str):
    """Get the backend instance by name from a list of backends.
    
    Args:
        backend_name: Name of the backend to find
        
    Returns:
        Backend instance with the given name, or None if not found
    """
    available_backends = get_configured_backends()
    for backend in available_backends:
        if backend.name == backend_name:
            return backend
    return None


@cli.command()
@click.argument('query')
@click.option('-e', '--exact', is_flag=True, help='Show only exact matches')
def search(query: str, exact: bool):
    """Search for packages across all available sources.
    
    Example:
        upk search firefox
    """
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.spinner import Spinner
    
    # Initialize and filter backends
    available_backends = get_configured_backends()
    
    if not available_backends:
        click.echo("Error: No package managers available!", err=True)
        return
    
    # Track backend status
    backend_status = {b.name: Spinner("dots", text="searching...", style="cyan") for b in available_backends}
    console = Console()
    
    def update_progress(backend_name: str, success: bool):
        """Update backend status when it completes."""
        backend_status[backend_name] = "✓ done" if success else "✗ failed"
    
    def generate_status_table():
        """Generate status table for live display."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", no_wrap=True)
        table.add_column(style="dim")
        
        table.add_row(f"Searching for:", f'"{query}"')
        for backend_name, status in backend_status.items():
            table.add_row(f"  {backend_name}:", status)
        
        return table
    
    # Perform search with live progress
    with Live(generate_status_table(), console=console, refresh_per_second=10) as live:
        results = search_all_backends(available_backends, query, update_progress)
        live.update(generate_status_table())
        
    if exact:
        results = [pkg for pkg in results if pkg.name == query]
    
    # Display results
    display_search_results(results)


def install_package(package_name: str, exact: bool = False, extra_args: list = None) -> bool:
    """Install a package by name from available sources.
    
    Args:
        package_name: Name of the package to install
        exact: If True, only show exact matches
        extra_args: Optional list of extra arguments to pass to the backend
        
    Returns:
        True if installation was successful, False otherwise
    """
    from rich.prompt import Prompt
    from rich.console import Console
    console = Console()
    
    if extra_args is None:
        extra_args = []
    
    available_backends = get_configured_backends()
    
    if not available_backends:
        console.print("[red]Error: No package managers available![/red]")
        return False
    
    # Search for matching packages to offer a prompt
    console.print(f"Searching for [bold cyan]{package_name}[/bold cyan] across available sources...")
    
    from search import search_all_backends
    results = search_all_backends(available_backends, package_name)
    
    # Filter for exact matches if requested
    if exact:
        results = [pkg for pkg in results if pkg.name == package_name]
    
    sorted_results = display_search_results(results, show_numbers=True)
    
    if not sorted_results:
        return False
        
    choice = Prompt.ask(
        "Enter the number of the package to install (or 'q' to cancel)",
        choices=[str(i) for i in range(1, len(sorted_results) + 1)] + ['q'],
        show_choices=False
    )
    
    if choice.lower() == 'q':
        console.print("Installation cancelled.")
        return False
        
    selected_pkg = sorted_results[int(choice) - 1]
    
    target_backend = get_backend_from_name(selected_pkg.source)
    if not target_backend:
        console.print(f"[red]Error: Selected source '{selected_pkg.source}' is not available.[/red]")
        return False
        
    console.print(f"Installing [bold cyan]{selected_pkg.name}[/bold cyan] using [bold blue]{selected_pkg.source}[/bold blue]...")
    success = target_backend.install(selected_pkg.name, extra_args=extra_args)
    if success:
        console.print(f"[green]Successfully installed {selected_pkg.name}.[/green]")
    else:
        console.print(f"[red]Failed to install {selected_pkg.name}.[/red]")
    return success


def install_local_file(file_path: str, extra_args: list = None) -> bool:
    """Install a local file by determining its type and routing to appropriate backend.
    
    Args:
        file_path: Path to the local file to install
        extra_args: Optional list of extra arguments to pass to the backend
        
    Returns:
        True if installation was successful, False otherwise
    """
    from rich.console import Console
    console = Console()
    
    if extra_args is None:
        extra_args = []
    
    import os
    from utils import detect_file_type, get_appimages_dir
    
    absolute_path = os.path.abspath(file_path)
    detected_source = detect_file_type(absolute_path)
        
    if not detected_source:
        console.print(f"[red]✗ Unknown file type for: {absolute_path}[/red]")
        return False
    
    target_backend = get_backend_from_name(detected_source)
    if not target_backend:
        console.print(f"[red]✗ No available backend for {detected_source} files[/red]")
        return False
    
    console.print(f"[bold blue]Routing to {detected_source} backend...[/bold blue]")
    
    # Pass the file path to the backend's handle_local_file method
    if hasattr(target_backend, 'handle_local_file'):
        success = target_backend.handle_local_file(absolute_path)
    else:
        success = target_backend.install(absolute_path, extra_args=extra_args)
        
    if success:
        console.print(f"[green]Successfully installed {file_path}.[/green]")
    else:
        console.print(f"[red]Failed to install {file_path}.[/red]")
    return success


def install_remote_file(url: str, extra_args: list = None) -> bool:
    """Install a remote file by downloading it first, then installing the local file.
    
    Args:
        url: URL of the remote file to download and install
        extra_args: Optional list of extra arguments to pass to the backend
        
    Returns:
        True if installation was successful, False otherwise
    """
    from rich.console import Console
    console = Console()
    
    if extra_args is None:
        extra_args = []
    
    from utils import download_remote_file, cleanup_downloads
    
    # 1. Download the file
    downloaded_file = download_remote_file(url)
    if not downloaded_file:
        console.print(f"[red]Failed to download {url}.[/red]")
        return False
        
    try:
        # 2. Install the downloaded file
        success = install_local_file(downloaded_file, extra_args=extra_args)
        return success
        
    finally:
        # Clean up downloads directory
        cleanup_downloads()


@cli.command()
@click.argument('package')
@click.option('-e', '--exact', is_flag=True, help='Show only exact matches')
@click.argument('extra_args', nargs=-1)
def install(package: str, exact: bool, extra_args: tuple):
    """Install a package, local file, or remote file.
    
    The install command automatically determines the type of input:
    - Package name (e.g., 'firefox') → Searches available sources
    - Local file path (e.g., './app.deb') → Installs the local file
    - Remote URL (e.g., 'https://example.com/app.deb') → Downloads and installs
    
    Extra arguments are passed to the backend (e.g., --classic for snap).
    
    Example:
        upk install firefox
        upk install ./myapp.deb
        upk install https://example.com/myapp.deb
        upk install fresh-editor --classic
    """
    from rich.console import Console
    console = Console()
    
    import os
    from urllib.parse import urlparse
    from utils import is_local_file
    
    # Convert extra_args tuple to list
    extra = list(extra_args)
    
    # Determine what type of install this is
    parsed_url = urlparse(package)
    
    if parsed_url.scheme in ('http', 'https'):
        # Remote file
        console.print(f"Installing remote file: [bold cyan]{package}[/bold cyan]")
        success = install_remote_file(package, extra_args=extra)
    elif is_local_file(package):
        # Local file
        console.print(f"Installing local file: [bold cyan]{package}[/bold cyan]")
        success = install_local_file(package, extra_args=extra)
    else:
        # Package name
        console.print(f"Installing package: [bold cyan]{package}[/bold cyan]")
        success = install_package(package, exact=exact, extra_args=extra)
    
    return success


@cli.command()
def update():
    """Update package lists and repositories.
    
    Updates the local system's cache of available packages.
    """
    from rich.console import Console
    console = Console()
    
    available_backends = get_configured_backends()
        
    for backend in available_backends:
        console.print(f"Updating package lists for [bold blue]{backend.name}[/bold blue]...")
        success = backend.update()
        if success:
            console.print(f"[green]Successfully updated lists for {backend.name}.[/green]")
        else:
            console.print(f"[red]Failed to update lists for {backend.name}.[/red]")


@cli.command()
@click.argument('package', required=False)
def upgrade(package: str):
    """Upgrade all packages or a specific package.
    
    If no package is specified, upgrades all installed packages system-wide.
    If a package is specified, attempts an isolated upgrade for only that target.
    """
    from rich.console import Console
    console = Console()
    
    available_backends = get_configured_backends()
        
    if package:
        console.print(f"Checking where [bold cyan]{package}[/bold cyan] is installed...")
        from search import search_all_backends
        results = search_all_backends(available_backends, package)
        installed_sources = {pkg.source for pkg in results if pkg.name == package and pkg.is_installed}
        
        if not installed_sources:
            console.print(f"[yellow]No installed exact match for '{package}' found in any selected source.[/yellow]")
            return
            
        available_backends = [b for b in available_backends if b.name in installed_sources]
        
    for backend in available_backends:
        target = f"'{package}'" if package else "all packages"
        console.print(f"Upgrading {target} via [bold blue]{backend.name}[/bold blue]...")
        success = backend.upgrade(package)
        if success:
            console.print(f"[green]Successfully upgraded via {backend.name}.[/green]")
        else:
            console.print(f"[red]Failed to upgrade via {backend.name}.[/red]")


@cli.command()
@click.argument('package')
def remove(package: str):
    """Remove a package."""
    from rich.prompt import Prompt
    from rich.console import Console
    console = Console()
    
    available_backends = get_configured_backends()
        
    console.print(f"Searching for [bold cyan]{package}[/bold cyan] among installed packages...")
    from search import list_all_backends
    results = list_all_backends(available_backends)
    
    # Check for exact case-insensitive match first
    exact_results = [pkg for pkg in results if pkg.name.lower() == package.lower()]
    if exact_results:
        results = exact_results
    else:
        # Fallback to substring match
        results = [pkg for pkg in results if package.lower() in pkg.name.lower()]
    
    if not results:
        console.print(f"[yellow]No installed match for '{package}' found.[/yellow]")
        return
        
    if len(results) == 1:
        chosen_pkg = results[0]
        console.print(f"Found installed in {chosen_pkg.source}, removing...")
    else:
        from display import display_search_results
        sorted_results = display_search_results(results, show_numbers=True)
        choice = Prompt.ask(
            "Enter the number of the package to remove (or 'q' to cancel)", 
            choices=[str(i) for i in range(1, len(sorted_results) + 1)] + ['q'], 
            show_choices=False
        )
        if choice.lower() == 'q':
            console.print("Removal cancelled.")
            return
        chosen_pkg = sorted_results[int(choice) - 1]
        
    target_backend = get_backend_from_name(chosen_pkg.source)
    success = target_backend.remove(chosen_pkg.name)
    if success:
        console.print(f"[green]Successfully removed {chosen_pkg.name}.[/green]")
    else:
        console.print(f"[red]Failed to remove {package}.[/red]")


@cli.command(name="list")
@click.argument('package', required=False)
@click.option('-e', '--exact', is_flag=True, help='Show only exact matches')
def list_pkgs(package: str, exact: bool):
    """List all installed packages across all package managers."""
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.spinner import Spinner
    from search import list_all_backends
    
    available_backends = get_configured_backends()
    
    backend_status = {b.name: Spinner("dots", text="listing...", style="cyan") for b in available_backends}
    console = Console()
    
    def update_progress(backend_name: str, success: bool):
        backend_status[backend_name] = "✓ done" if success else "✗ failed"
    
    def generate_status_table():
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", no_wrap=True)
        table.add_column(style="dim")
        table.add_row(f"Listing packages:")
        for backend_name, status in backend_status.items():
            table.add_row(f"  {backend_name}:", status)
        return table
    
    with Live(generate_status_table(), console=console, refresh_per_second=10) as live:
        results = list_all_backends(available_backends, update_progress)
        live.update(generate_status_table())
    
    if package:
        if exact:
            results = [pkg for pkg in results if pkg.name == package]
        else:
            results = [pkg for pkg in results if package.lower() in pkg.name.lower()]
            
    display_search_results(results)


@cli.command()
@click.argument('action', type=click.Choice(['get', 'set', 'list']))
@click.argument('key', required=False)
@click.argument('value', required=False)
def config(action: str, key: str, value: str):
    """Manage UPK configuration.
    
    Actions:
      get <key>          - Display the value of a configuration key
      set <key> <value>  - Change the value of a configuration key
      list               - Show all configuration keys and values
      
    Available keys:
      backends_priority (JSON list)
      disabled_backends (JSON list)
      always_exact_search (true/false)
      interactive_prompts (true/false)
    """
    import json
    from config import load_config, set_value, DEFAULT_CONFIG
    from rich.console import Console
    console = Console()
    
    loaded = load_config()
    
    if action == 'list':
        for k, v in loaded.items():
            console.print(f"[bold cyan]{k}[/bold cyan] = {json.dumps(v)}")
        return
        
    if action == 'get':
        if not key:
            console.print("[red]Error: 'key' is required for get action.[/red]")
            return
        if key not in DEFAULT_CONFIG:
            console.print(f"[red]Error: Unknown key '{key}'.[/red]")
            return
        console.print(f"[bold cyan]{key}[/bold cyan] = {json.dumps(loaded.get(key))}")
        return
        
    if action == 'set':
        if not key or not value:
            console.print("[red]Error: both 'key' and 'value' are required for set action.[/red]")
            return
        
        if key not in DEFAULT_CONFIG:
            console.print(f"[red]Error: Unknown key '{key}'.[/red]")
            return
            
        # Parse value based on type of default
        default_val = DEFAULT_CONFIG[key]
        parsed_value = value
        
        try:
            if isinstance(default_val, bool):
                parsed_value = value.lower() in ('true', '1', 't', 'y', 'yes')
            elif isinstance(default_val, list):
                # Try parsing as JSON list, fallback to comma-separated string
                if value.startswith('[') and value.endswith(']'):
                    parsed_value = json.loads(value)
                else:
                    parsed_value = [v.strip() for v in value.split(',')]
            elif isinstance(default_val, int):
                parsed_value = int(value)
        except Exception as e:
            console.print(f"[red]Error parsing value for {key}: {e}[/red]")
            return
            
        set_value(key, parsed_value)
        console.print(f"[green]Successfully set [bold cyan]{key}[/bold cyan] to {json.dumps(parsed_value)}[/green]")


if __name__ == "__main__":
    cli()
