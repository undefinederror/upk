#!/usr/bin/env python3
"""Utilities for UPK - centralized file type detection and path management."""

import os
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from rich.console import Console
from rich.progress import Progress, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from .config import load_config


def detect_file_type(file_path: str) -> Optional[str]:
    """Detect the file type and determine which backend should handle it.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Backend name that should handle this file type, or None if unknown
    """
    file_path_lower = file_path.lower()
    
    if file_path_lower.endswith('.deb'):
        return 'apt'
    elif file_path_lower.endswith('.appimage'):
        return 'appimage'
    elif file_path_lower.endswith('.snap'):
        return 'snap'
    elif file_path_lower.endswith('.flatpakref'):
        return 'flatpak'
    elif file_path_lower.endswith('.pacstall'):
        return 'pacstall'
    
    return None


def get_downloads_dir() -> Path:
    """Get the configured downloads directory.
    
    Returns:
        Path to the downloads directory
    """
    config = load_config()
    downloads_path = config.get("path_downloads", "~/.local/share/upk/downloads")
    return Path(downloads_path).expanduser()


def get_appimages_dir() -> Path:
    """Get the configured AppImages directory.
    
    Returns:
        Path to the AppImages directory
    """
    config = load_config()
    appimages_path = config.get("path_appimages", "~/.local/share/applications/AppImages")
    return Path(appimages_path).expanduser()


def is_local_file(file_path: str) -> bool:
    """Check if the given path is a local file.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if it's a local file, False otherwise
    """
    return Path(file_path).exists() and Path(file_path).is_file()


def download_remote_file(url: str) -> Optional[str]:
    """Download a remote file to the downloads directory.
    
    Args:
        url: URL of the file to download
        
    Returns:
        Path to the downloaded file, or None if download failed
    """
    console = Console()
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ('http', 'https'):
        return None
        
    downloads_dir = get_downloads_dir()
    downloads_dir.mkdir(parents=True, exist_ok=True)
    
    filename = os.path.basename(parsed_url.path) or "downloaded_package"
    download_path = downloads_dir / filename
    
    console.print(f"[bold green]Downloading[/bold green]: [cyan]{url}[/cyan]")
    console.print(f"[dim]Saving to: {download_path}[/dim]")
    
    try:
        with Progress(
            "[progress.description]{task.description}",
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            def reporthook(block_num, block_size, total_size):
                if total_size <= 0:
                    return
                downloaded = block_num * block_size
                if downloaded >= total_size:
                    progress.update(task_id, completed=total_size)
                else:
                    progress.update(task_id, completed=downloaded)
            
            task_id = progress.add_task(f"Downloading {filename}", total=0)
            urllib.request.urlretrieve(url, download_path, reporthook)
            
        console.print(f"[green]✓ Download complete: {download_path}[/green]")
        return str(download_path)
        
    except Exception as e:
        console.print(f"[red]✗ Download failed: {e}[/red]")
        # Clean up partial download
        if download_path.exists():
            download_path.unlink()
        return None


def cleanup_downloads() -> None:
    """Clean up all downloads after installation."""
    console = Console()
    downloads_dir = get_downloads_dir()
    
    try:
        files = list(downloads_dir.glob('*'))
        for file in files:
            try:
                file.unlink()
                console.print(f"[dim]Cleaned up download: {file.name}[/dim]")
            except OSError:
                pass
                
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to cleanup downloads: {e}[/yellow]")
