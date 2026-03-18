"""Snap backend."""

import subprocess
from typing import List, Optional

from .base import Backend, PackageInfo


class SnapBackend(Backend):
    """Backend for Snap package manager."""

    @property
    def name(self) -> str:
        return "snap"

    def __init__(self):
        self._installed_cache: Optional[dict] = None

    def is_available(self) -> bool:
        """Check if Snap is available."""
        try:
            subprocess.run(
                ["which", "snap"],
                capture_output=True,
                check=True,
                timeout=2
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def search(self, query: str) -> List[PackageInfo]:
        """Search for packages using snap find."""
        if not self.is_available():
            return []

        try:
            result = subprocess.run(
                ["snap", "find", query],
                capture_output=True,
                text=True,
                timeout=10
            )
            return self._parse_search_output(result.stdout, query)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _parse_search_output(self, output: str, query: Optional[str] = None) -> List[PackageInfo]:
        """Parse snap find output."""
        packages = []
        if query:
            query = query.lower()
        lines = output.split('\n')
        
        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue
            
            # snap find output format (columns separated by spaces):
            # Name  Version  Publisher  Notes  Summary
            parts = line.split()
            if len(parts) >= 2:
                package_name = parts[0]
                version = parts[1]
                description = ' '.join(parts[4:]) if len(parts) >= 5 else None
                
                
                # Filter matches if query is provided - make sure it's in name or summary
                # to avoid publisher-only matches
                if query:
                    summary_text = description.lower() if description else ""
                    if query not in package_name.lower() and query not in summary_text:
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
        """Load all installed snaps into cache."""
        if not self.is_available():
            self._installed_cache = {}
            return

        try:
            result = subprocess.run(
                ["snap", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._installed_cache = {}
            lines = result.stdout.split('\n')
            for line in lines[1:]:  # Skip header
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1]
                    
                    # Try to get summary from local metadata (fast)
                    summary = None
                    try:
                        yaml_path = f"/snap/{name}/current/meta/snap.yaml"
                        import os
                        if os.path.exists(yaml_path):
                            with open(yaml_path, 'r') as f:
                                for l in f:
                                    if l.startswith("summary:"):
                                        summary = l.split(":", 1)[1].strip()
                                        break
                    except Exception:
                        pass
                        
                    self._installed_cache[name] = {
                        "version": version,
                        "description": summary
                    }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._installed_cache = {}

    def get_installed_version(self, package_name: str) -> Optional[str]:
        """Get installed version using cache (or fallback)."""
        if self._installed_cache is not None:
            info = self._installed_cache.get(package_name)
            return info["version"] if info else None

        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                ["snap", "list", package_name],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # snap list output format:
            # Name  Version  Rev  Tracking  Publisher  Notes
            lines = result.stdout.split('\n')
            for line in lines[1:]:  # Skip header
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[0] == package_name:
                    return parts[1]
            
            return None
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def install(self, package_name: str, extra_args: List[str] = None) -> bool:
        """Install a package using snap."""
        if not self.is_available():
            return False
        
        if extra_args is None:
            extra_args = []
            
        try:
            # extra_args go BEFORE the package name for snap
            cmd = ["sudo", "snap", "install"] + extra_args + [package_name]
            result = subprocess.run(cmd)
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def update(self) -> bool:
        """Update package lists using snap."""
        if not self.is_available():
            return False
            
        return True

    def upgrade(self, package_name: Optional[str] = None) -> bool:
        """Upgrade packages using snap."""
        if not self.is_available():
            return False
            
        try:
            cmd = ["sudo", "snap", "refresh"]
            if package_name:
                cmd.append(package_name)
            result = subprocess.run(cmd)
            return result.returncode == 0
        except KeyboardInterrupt:
            return False
        except Exception:
            return False

    def remove(self, package_name: str) -> bool:
        """Remove a package using snap."""
        if not self.is_available():
            return False
            
        try:
            result = subprocess.run(["sudo", "snap", "remove", package_name])
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
