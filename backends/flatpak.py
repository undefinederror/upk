"""Flatpak backend."""

import subprocess
from typing import List, Optional

from .base import Backend, PackageInfo


class FlatpakBackend(Backend):
    """Backend for Flatpak package manager."""

    @property
    def name(self) -> str:
        return "flatpak"

    def __init__(self):
        self._installed_cache: Optional[dict] = None

    def is_available(self) -> bool:
        """Check if Flatpak is available."""
        try:
            subprocess.run(
                ["which", "flatpak"],
                capture_output=True,
                check=True,
                timeout=2
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def search(self, query: str) -> List[PackageInfo]:
        """Search for packages using flatpak search."""
        if not self.is_available():
            return []

        # We no longer pre-fetch installed cache here
        try:
            result = subprocess.run(
                ["flatpak", "search", query, "--columns=application,version,description"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return self._parse_search_output(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _parse_search_output(self, output: str) -> List[PackageInfo]:
        """Parse flatpak search output."""
        packages = []
        lines = output.split('\n')
        
        # Output format is defined by --columns=application,version,description
        # Note: flatpak doesn't print a header if you specify columns
        # Or wait, sometimes it does. We will split by \t since --columns outputs tab-separated or space separated
        for line in lines:
            if not line.strip():
                continue
                
            if "no matches found" in line.lower():
                continue
            
            # Application    Version    Description
            # org.mozilla.firefox    121.0    Mozilla Firefox
            parts = line.split('\t')
            if len(parts) >= 2:
                # Some flatpak versions use spaces instead of tabs depending on output mode
                package_name = parts[0].strip()
                version = parts[1].strip()
                description = parts[2].strip() if len(parts) >= 3 else None
                
                # Header check just in case
                if package_name.lower() == "application ID".lower() or package_name.lower() == "application":
                    continue
                
                if not package_name:
                    continue
                    
                # Fix version if empty
                if not version:
                    version = "unknown"
                
                
                packages.append(PackageInfo(
                    name=package_name,
                    version=version,
                    source=self.name,
                    description=description,
                    installed_version=None
                ))
            else:
                # Fallback to splitting by space if tab split didn't work
                parts = line.split()
                if len(parts) >= 2:
                    package_name = parts[0]
                    version = parts[1]
                    description = ' '.join(parts[2:]) if len(parts) > 2 else None
                    
                    if package_name.lower() == "application" or package_name.lower() == "application ID":
                        continue
                        
                    
                    packages.append(PackageInfo(
                        name=package_name,
                        version=version,
                        source=self.name,
                        description=description,
                        installed_version=None
                    ))
        
        return packages

    def _load_installed_cache(self) -> None:
        """Load all installed flatpaks into cache."""
        if not self.is_available():
            self._installed_cache = {}
            return

        try:
            result = subprocess.run(
                ["flatpak", "list", "--app", "--columns=application,version,description"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._installed_cache = {}
            lines = result.stdout.split('\n')
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    self._installed_cache[parts[0].strip()] = {
                        "version": parts[1].strip() or "installed",
                        "description": parts[2].strip() if len(parts) >= 3 else None
                    }
                else:
                    parts = line.split()
                    if len(parts) >= 2:
                        self._installed_cache[parts[0]] = {
                            "version": parts[1],
                            "description": ' '.join(parts[2:]) if len(parts) > 2 else None
                        }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._installed_cache = {}

    def get_installed_version(self, package_name: str) -> Optional[str]:
        """Get installed version using cache."""
        if self._installed_cache is not None:
            info = self._installed_cache.get(package_name)
            return info["version"] if info else None
        
        if not self.is_available():
            return None
            
        self._load_installed_cache()
        info = self._installed_cache.get(package_name)
        return info["version"] if info else None

    def install(self, package_name: str, extra_args: List[str] = None) -> bool:
        """Install a package using flatpak."""
        if not self.is_available():
            return False
        
        if extra_args is None:
            extra_args = []
            
        try:
            cmd = ["flatpak", "install", "-y", "flathub"] + extra_args + [package_name]
            result = subprocess.run(cmd)
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def update(self) -> bool:
        """Update package lists using flatpak."""
        if not self.is_available():
            return False
            
        try:
            result = subprocess.run(["flatpak", "update", "--appstream", "-y"])
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def upgrade(self, package_name: Optional[str] = None) -> bool:
        """Upgrade packages using flatpak."""
        if not self.is_available():
            return False
            
        try:
            cmd = ["flatpak", "update", "-y"]
            if package_name:
                cmd.append(package_name)
            result = subprocess.run(cmd)
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def remove(self, package_name: str) -> bool:
        """Remove a package using flatpak."""
        if not self.is_available():
            return False
            
        try:
            result = subprocess.run(["flatpak", "uninstall", "-y", package_name])
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def list_packages(self) -> List[PackageInfo]:
        """List installed packages."""
        if not self.is_available():
            return []
            
        self._load_installed_cache()
        if not self._installed_cache:
            return []
            
        packages = []
        for name, info in self._installed_cache.items():
            packages.append(PackageInfo(
                name=name,
                version=info["version"],
                source=self.name,
                description=info.get("description"),
                installed_version=info["version"]
            ))
        return packages
