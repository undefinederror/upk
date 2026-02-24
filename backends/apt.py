"""APT backend using Nala (with fallback to apt)."""

import re
import subprocess
from typing import List, Optional

from .base import Backend, PackageInfo


class AptBackend(Backend):
    """Backend for APT package manager using Nala."""

    @property
    def name(self) -> str:
        return "apt"

    def __init__(self):
        self._installed_cache: Optional[dict] = None

    def is_available(self) -> bool:
        """Check if APT is available (it always is on Ubuntu)."""
        return True

    def _has_nala(self) -> bool:
        """Check if Nala is installed."""
        try:
            subprocess.run(
                ["which", "nala"],
                capture_output=True,
                check=True,
                timeout=2
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def search(self, query: str) -> List[PackageInfo]:
        """Search for packages using Nala or apt."""
        # Pre-fetch installed cache once per search
        self._load_installed_cache()
        
        if self._has_nala():
            return self._search_nala(query)
        else:
            return self._search_apt(query)

    def _search_nala(self, query: str) -> List[PackageInfo]:
        """Search using Nala."""
        try:
            result = subprocess.run(
                ["nala", "search", query],
                capture_output=True,
                text=True,
                timeout=10
            )
            return self._parse_search_output(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _search_apt(self, query: str) -> List[PackageInfo]:
        """Search using apt as fallback."""
        try:
            result = subprocess.run(
                ["apt", "search", query],
                capture_output=True,
                text=True,
                timeout=10,
                env={"LANG": "C"}  # Force English output
            )
            return self._parse_search_output(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _parse_search_output(self, output: str) -> List[PackageInfo]:
        """Parse search output from Nala or apt."""
        packages = []
        
        # Nala format: package-name version [repo/section]
        # Example: libvlc5 3.0.21-11 [Ubuntu/questing universe]
        nala_pattern = r'^([a-zA-Z0-9][a-zA-Z0-9+._-]+)\s+(\S+)\s+\['
        
        # APT format: package-name/repo version arch
        # Example: firefox/jammy-updates 121.0+build1-0ubuntu0.22.04.1 amd64
        apt_pattern = r'^([a-zA-Z0-9][a-zA-Z0-9+._-]+)/\S+\s+(\S+)'
        
        for line in output.split('\n'):
            # Try Nala format first
            match = re.match(nala_pattern, line)
            if not match:
                # Try APT format
                match = re.match(apt_pattern, line)
            
            if match:
                package_name = match.group(1)
                version = match.group(2)
                
                # Get installed version from cache
                installed_version = self.get_installed_version(package_name)
                
                packages.append(PackageInfo(
                    name=package_name,
                    version=version,
                    source=self.name,
                    installed_version=installed_version
                ))
        
        return packages

    def _load_installed_cache(self) -> None:
        """Load all installed packages into cache."""
        try:
            # dpkg-query -W -f='${Package} ${Version}\n'
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${Package} ${Version}\n"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._installed_cache = {}
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        self._installed_cache[parts[0]] = parts[1]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._installed_cache = {}

    def get_installed_version(self, package_name: str) -> Optional[str]:
        """Get installed version using cache (or fallback)."""
        if self._installed_cache is not None:
            return self._installed_cache.get(package_name)
            
        # Fallback to single command if cache not loaded
        try:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${Version}", package_name],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def install(self, package_name: str) -> bool:
        """Install a package using Nala or apt."""
        if self._has_nala():
            cmd = ["sudo", "nala", "install", package_name]
        else:
            cmd = ["sudo", "apt", "install", package_name]
            
        try:
            result = subprocess.run(cmd)
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def update(self) -> bool:
        """Update package lists using Nala or apt."""
        if self._has_nala():
            cmd = ["sudo", "nala", "update"]
        else:
            cmd = ["sudo", "apt", "update"]
            
        try:
            result = subprocess.run(cmd)
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def upgrade(self, package_name: Optional[str] = None) -> bool:
        """Upgrade packages using Nala or apt."""
        if self._has_nala():
            if package_name:
                cmd = ["sudo", "nala", "install", package_name]
            else:
                cmd = ["sudo", "nala", "upgrade"]
        else:
            if package_name:
                cmd = ["sudo", "apt", "install", "--only-upgrade", "-y", package_name]
            else:
                cmd = ["sudo", "apt", "upgrade", "-y"]
            
        try:
            result = subprocess.run(cmd)
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def remove(self, package_name: str) -> bool:
        """Remove a package using Nala or apt."""
        if self._has_nala():
            cmd = ["sudo", "nala", "remove", package_name]
            
            # Check for history to undo
            try:
                import re
                history_result = subprocess.run(["nala", "history"], capture_output=True, text=True)
                lines = history_result.stdout.split('\n')
                last_install_id = None
                
                # Search backwards for the most recent install of this exact package
                for line in reversed(lines):
                    if not line.strip(): continue
                    match = re.match(r'^\s*(\d+)\s+install\s+(.+?)\s+\d{4}-', line)
                    if match:
                        tx_id = match.group(1)
                        pkgs = match.group(2).split()
                        if package_name in pkgs:
                            last_install_id = tx_id
                            break
                            
                if last_install_id:
                    from rich.console import Console
                    console = Console()
                    console.print(f"[yellow]Found Nala history transaction {last_install_id} for installing '{package_name}'.[/yellow]")
                    console.print("[yellow]Using 'nala history undo' to remove it and its orphaned dependencies.[/yellow]")
                    cmd = ["sudo", "nala", "history", "undo", str(last_install_id)]
            except Exception:
                pass
        else:
            cmd = ["sudo", "apt", "remove", package_name]
            
        try:
            result = subprocess.run(cmd)
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def list_packages(self) -> List[PackageInfo]:
        """List installed packages."""
        self._load_installed_cache()
        if not self._installed_cache:
            return []
            
        packages = []
        for name, version in self._installed_cache.items():
            packages.append(PackageInfo(
                name=name,
                version=version,
                source=self.name,
                installed_version=version
            ))
        return packages
