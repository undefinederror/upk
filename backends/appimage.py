import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from .base import Backend, PackageInfo
from utils import get_appimages_dir


class AppImageBackend(Backend):
    """AppImage backend using 'am' (Application Manager by ivan-hc)."""

    @property
    def name(self) -> str:
        return "appimage"

    def is_available(self) -> bool:
        """Check if 'am' or 'appman' is available on the system."""
        return shutil.which("am") is not None or shutil.which("appman") is not None

    def _run_am(self, args: List[str], capture: bool = True, input_text: str = None) -> subprocess.CompletedProcess:
        """Helper to run 'am' or 'appman' commands.
        
        Args:
            args: Command arguments
            capture: Whether to capture output
            input_text: Text to send to stdin (for interactive prompts)
        """
        tool = shutil.which("am") or shutil.which("appman")
        if not tool:
            raise RuntimeError("Neither 'am' nor 'appman' is installed.")
            
        cmd = [tool] + args
        return subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            check=False,
            input=input_text
        )

    def list_packages(self) -> List[PackageInfo]:
        """List installed AppImages using 'am -f' or 'am list'."""
        if not self.is_available():
            return []
            
        result = self._run_am(["-f"])
        if result.returncode != 0:
            return []

        packages: List[PackageInfo] = []
        
        # 1. Parse Managed section (Official DB)
        # Format: ◆ name | db | version | type | size
        managed_pattern = r'◆\s+([^\s|]+)\s+\|\s+([^\s|]+)\s+\|\s+([^\s|]+)\s+\|\s+([^\s|]+)'
        
        # 2. Parse Integrated section (Local files via --launcher)
        # Format: ◆ Filename | Path | Size
        integrated_pattern = r'◆\s+([^\s|]+)\s+\|\s+([^\s|]+)\s+\|\s+([^\s|]+)'
        
        # Track whether we are in the Integrated section
        in_integrated_section = False
        
        for line in result.stdout.splitlines():
            line = line.strip()
            if "YOU HAVE INTEGRATED" in line:
                in_integrated_section = True
                continue
                
            if line.startswith("◆"):
                if in_integrated_section:
                    match = re.search(integrated_pattern, line)
                    if match:
                        filename = match.group(1).strip()
                        # Use a cleaner name for local files if possible
                        name = filename.replace(".AppImage", "").replace("-AM", "")
                        packages.append(PackageInfo(
                            name=name,
                            version="local",
                            source=self.name,
                            installed_version="local"
                        ))
                else:
                    match = re.search(managed_pattern, line)
                    if match:
                        name = match.group(1).strip()
                        version = match.group(3).strip()
                        packages.append(PackageInfo(
                            name=name,
                            version=version,
                            source=self.name,
                            installed_version=version
                        ))
        return packages

    def get_installed_version(self, package_name: str) -> Optional[str]:
        """Get the version of an installed AppImage."""
        for pkg in self.list_packages():
            if pkg.name == package_name:
                return pkg.installed_version
        return None

    def search(self, query: str) -> List[PackageInfo]:
        """Search for AppImages using 'am -q'."""
        if not self.is_available():
            return []

        result = self._run_am(["-q", query])
        if result.returncode != 0:
            return []

        packages: List[PackageInfo] = []
        # Format: ◆ name : description
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("◆"):
                parts = line.split(":", 1)
                name = parts[0].replace("◆", "").strip()
                # am search doesn't show remote versions, so we use 'latest'
                packages.append(PackageInfo(
                    name=name,
                    version="latest",
                    source=self.name,
                    installed_version=self.get_installed_version(name)
                ))
        return packages

    def install(self, package: str, extra_args: List[str] = None) -> bool:
        """Install an AppImage.
        - If input is a path to a local file, copies to AppImages dir and runs 'am --launcher'.
        - Otherwise uses 'am -i' for remote install.
        """
        if not self.is_available():
            from rich.console import Console
            Console().print("[red]Error: Neither 'am' nor 'appman' is installed.[/red]")
            return False

        import os
        if os.path.exists(package) and os.path.isfile(package):
            # Copy to AppImages dir first
            appimages_dir = get_appimages_dir()
            appimages_dir.mkdir(parents=True, exist_ok=True)
            filename = os.path.basename(package)
            dest_path = appimages_dir / filename
            
            # Only copy if destination doesn't exist (don't overwrite)
            if not dest_path.exists():
                shutil.copy2(package, dest_path)
                dest_path.chmod(0o755)
            
            # Run --launcher on the copy in AppImages dir interactively
            # This allows the user to enter the command name when prompted
            args = ["--launcher", str(dest_path)]
            result = self._run_am(args, capture=False)
            return result.returncode == 0
        else:
            # Remote installation from database
            args = ["-i", package]
            
        result = self._run_am(args, capture=False)
        return result.returncode == 0

    def remove(self, package_name: str) -> bool:
        """Remove an AppImage.
        - If integrated locally, removes the `.desktop` file and bin symlink.
        - Otherwise, uses 'am -r'.
        """
        if not self.is_available():
            return False

        # Check if it is a local integrated app
        for pkg in self.list_packages():
            if pkg.name == package_name and pkg.version == "local":
                is_removed = False
                import os, glob, subprocess
                
                # Delete the desktop file created by am --launcher
                appimages_dir = get_appimages_dir()
                desktop_pattern = f"{appimages_dir}/{package_name}*.desktop"
                for d_file in glob.glob(desktop_pattern):
                    try:
                        os.remove(d_file)
                        is_removed = True
                    except OSError:
                        pass
                        
                # Delete corresponding symlinks in bin dir
                bin_dir = os.path.expanduser("~/.local/bin")
                if os.path.exists(bin_dir):
                    for bin_file in os.listdir(bin_dir):
                        bin_path = os.path.join(bin_dir, bin_file)
                        if os.path.islink(bin_path):
                            try:
                                target = os.readlink(bin_path)
                                if package_name in target:
                                    os.remove(bin_path)
                                    is_removed = True
                            except OSError:
                                pass
                
                # Delete the AppImage file from appimages directory
                safe_file = os.path.join(appimages_dir, f"{package_name}*.AppImage")
                for f in glob.glob(safe_file):
                    try:
                        os.remove(f)
                        is_removed = True
                    except Exception:
                        pass
                                
                # Check if there is an /opt directory for this app and remove it using sudo
                opt_dir = f"/opt/{package_name}"
                if os.path.exists(opt_dir):
                    try:
                        subprocess.run(["sudo", "rm", "-rf", opt_dir], check=False)
                        is_removed = True
                    except Exception:
                        pass
                
                # am -f cleans up orphaned launchers
                self._run_am(["-f"]) 
                return is_removed
            
        result = self._run_am(["-r", package_name], capture=False)
        # Handle cases where 'am' exits with 0 even if it failed
        # The true check is whether it was actually removed from list
        for pkg in self.list_packages():
            if pkg.name == package_name:
                return False
        return True

    def update(self) -> bool:
        """Sync 'am' database using 'am -s'."""
        if not self.is_available():
            return False
        result = self._run_am(["-s"], capture=False)
        return result.returncode == 0

    def upgrade(self, package_name: Optional[str] = None) -> bool:
        """Upgrade AppImages using 'am -u'."""
        if not self.is_available():
            return False
            
        args = ["-u"]
        if package_name:
            args.append(package_name)
        else:
            args.append("--apps") # Update only apps, not the manager itself
            
        result = self._run_am(args, capture=False)
        return result.returncode == 0
