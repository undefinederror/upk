"""Pacstall backend."""

import subprocess
from typing import List, Optional

from .base import Backend, PackageInfo


class PacstallBackend(Backend):
    """Backend for Pacstall package manager."""

    @property
    def name(self) -> str:
        return "pacstall"

    def __init__(self):
        self._installed_cache: Optional[dict] = None

    def is_available(self) -> bool:
        """Check if Pacstall is available."""
        try:
            subprocess.run(
                ["which", "pacstall"],
                capture_output=True,
                check=True,
                timeout=2
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def search(self, query: str) -> List[PackageInfo]:
        """Search for packages using pacstall -S."""
        if not self.is_available():
            return []

        try:
            result = subprocess.run(
                ["pacstall", "-S", query],
                capture_output=True,
                text=True,
                timeout=10
            )
            return self._parse_search_output(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _parse_search_output(self, output: str) -> List[PackageInfo]:
        """Parse pacstall search output."""
        import re
        
        # ANSI escape codes pattern (colors and OSC 8 hyperlinks)
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m|\x1b\]8;;.*?\x07')
        
        packages = []
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            line = ansi_pattern.sub('', line)

            # Output usually looks like:
            # package-name @ github:pacstall/pacstall-programs
            parts = line.split('@')
            if len(parts) >= 1:
                package_name = parts[0].strip()
                
                # Pacstall search doesn't show version, so default to unknown
                version = "unknown"

                packages.append(PackageInfo(
                    name=package_name,
                    version=version,
                    source=self.name,
                    description=None,
                    installed_version=None
                ))

        return packages

    def _load_installed_cache(self) -> None:
        """Load all installed pacstall packages into cache."""
        if not self.is_available():
            self._installed_cache = {}
            return

        try:
            result = subprocess.run(
                ["pacstall", "-L"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._installed_cache = {}
            import os
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                name = None
                version = "unknown"
                
                if line.startswith('~ '):
                    line = line[len('~ '):].strip()
                    parts = line.split('@')
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        version = parts[1].strip()
                else:
                    name = line
                
                if name:
                    # Try to get version and description from metadata file if unknown
                    if version == "unknown":
                        metadata_path = f"/var/lib/pacstall/metadata/{name}"
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r') as f:
                                    for meta_line in f:
                                        if meta_line.startswith('_version='):
                                            version = meta_line.split('=', 1)[1].strip().strip('"').strip("'")
                                            break
                            except Exception:
                                pass
                                
                    self._installed_cache[name] = {
                        "version": version,
                        "description": None 
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
        return self._installed_cache.get(package_name)

    def install(self, package_name: str, extra_args: List[str] = None) -> bool:
        """Install a package using pacstall."""
        if not self.is_available():
            return False
        
        if extra_args is None:
            extra_args = []
            
        try:
            cmd = ["sudo", "pacstall", "-I"] + extra_args + [package_name, "-P"]
            result = subprocess.run(cmd)
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def update(self) -> bool:
        """Update package lists using pacstall."""
        if not self.is_available():
            return False
            
        try:
            result = subprocess.run(["sudo", "pacstall", "-U"])
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def upgrade(self, package_name: Optional[str] = None) -> bool:
        """Upgrade packages using pacstall."""
        if not self.is_available():
            return False
            
        try:
            if package_name:
                cmd = ["sudo", "pacstall", "-I", package_name, "-P"]
            else:
                cmd = ["sudo", "pacstall", "-Up", "-P"]
            result = subprocess.run(cmd)
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def remove(self, package_name: str) -> bool:
        """Remove a package using pacstall."""
        if not self.is_available():
            return False
            
        try:
            result = subprocess.run(["sudo", "pacstall", "-R", package_name, "-P"])
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
