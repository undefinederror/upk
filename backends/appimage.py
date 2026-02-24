"""AppImage backend for UPK.

This backend treats each AppImage file as a standalone package.
It scans a user‑configurable directory (default: ~/.local/appimages) for
files ending with `.AppImage`. The filename is expected to follow the
convention `<name>-<version>.AppImage` or simply `<name>.AppImage`.

Supported operations:
- `is_available` – true if the directory exists.
- `list_packages` – returns a list of `PackageInfo` objects for each AppImage.
- `install` – copies a local file into the directory (or downloads from a URL).
- `remove` – deletes the AppImage file.
- `search` – searches the public AppImageHub index for matching names.
- `update` / `upgrade` – no‑op (AppImages are self‑contained).
"""

import subprocess
from pathlib import Path
from typing import List, Optional

from .base import Backend, PackageInfo

DEFAULT_APPIMAGE_DIR = Path.home() / ".local" / "appimages"


class AppImageBackend(Backend):

    def __init__(self, directory: Optional[Path] = None):
        self.directory = Path(directory) if directory else DEFAULT_APPIMAGE_DIR
        self.directory.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "appimage"

    def is_available(self) -> bool:
        """AppImage backend is available if the directory exists."""
        return self.directory.is_dir()

    def _parse_filename(self, filename: str) -> PackageInfo:
        """Parse `<name>-<version>.AppImage` or `<name>.AppImage`.
        Returns a PackageInfo with `source` set to ``self.name``.
        """
        # Use removesuffix to correctly strip the extension (rstrip strips chars, not substrings)
        stem = filename.removesuffix(".AppImage")
        if "-" in stem:
            name, version = stem.rsplit("-", 1)
        else:
            name, version = stem, "unknown"
        return PackageInfo(
            name=name,
            version=version,
            source=self.name,
            installed_version=version,  # present on disk = installed
        )

    def list_packages(self) -> List[PackageInfo]:
        """List all AppImage files in the directory."""
        if not self.is_available():
            return []
        packages: List[PackageInfo] = []
        for entry in self.directory.iterdir():
            if entry.is_file() and entry.name.endswith(".AppImage"):
                packages.append(self._parse_filename(entry.name))
        return packages

    def get_installed_version(self, package_name: str) -> Optional[str]:
        """Return the version of an installed AppImage, or None if not found."""
        for pkg in self.list_packages():
            if pkg.name == package_name:
                return pkg.installed_version
        return None

    def install(self, package_path: str) -> bool:
        """Install an AppImage using the external `appimage-installer` CLI.
        The argument can be a local path or a remote URL – the installer handles both.
        """
        try:
            result = subprocess.run(["appimage-installer", package_path])
            return result.returncode == 0
        except Exception:
            return False

    def remove(self, package_name: str) -> bool:
        """Remove an AppImage by deleting its file from the managed directory.
        ``package_name`` should be the base name without the `.AppImage` suffix.
        """
        for entry in self.directory.iterdir():
            if entry.is_file() and entry.name.endswith(".AppImage"):
                stem = entry.name.removesuffix(".AppImage")
                # Match on the name part (before the last '-<version>')
                candidate_name = stem.rsplit("-", 1)[0] if "-" in stem else stem
                if candidate_name == package_name:
                    try:
                        entry.unlink()
                        return True
                    except Exception:
                        return False
        # Fallback: try external tool
        try:
            result = subprocess.run(["appimaged-cli", "remove", package_name])
            return result.returncode == 0
        except Exception:
            return False

    # AppImages are self‑contained; update/upgrade are no‑ops.
    def update(self) -> bool:
        return True

    def upgrade(self, package_name: Optional[str] = None) -> bool:
        return True

    # ------------------------------------------------------------------
    # Remote helpers
    # ------------------------------------------------------------------
    def search_remote(self, query: str) -> List[str]:
        """Search AppImageHub via the external `appimage-manager` CLI.
        Returns a list of download URLs that match *query*.
        """
        try:
            result = subprocess.run(
                ["appimage-manager", "search", query],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return []
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except Exception:
            return []

    def search(self, query: str) -> List[PackageInfo]:
        """Search for AppImages via external `appimage-manager`.
        Returns a list of ``PackageInfo`` objects built from the URLs returned
        by ``search_remote``.
        """
        urls = self.search_remote(query)
        results: List[PackageInfo] = []
        for url in urls:
            filename = url.split("/")[-1]
            info = self._parse_filename(filename)
            # Store the download URL as the version for display purposes
            info.version = url
            results.append(info)
        return results
