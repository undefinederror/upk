"""Base class for package manager backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PackageInfo:
    """Information about a package from a backend."""
    name: str
    version: str
    source: str
    description: Optional[str] = None
    installed_version: Optional[str] = None

    @property
    def is_installed(self) -> bool:
        """Check if package is installed."""
        return self.installed_version is not None


class Backend(ABC):
    """Abstract base class for package manager backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this backend (e.g., 'apt', 'snap')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available on the system."""
        pass

    @abstractmethod
    def search(self, query: str) -> List[PackageInfo]:
        """
        Search for packages matching the query.
        
        Args:
            query: Search term
            
        Returns:
            List of PackageInfo objects
        """
        pass

    @abstractmethod
    def get_installed_version(self, package_name: str) -> Optional[str]:
        """
        Get the installed version of a package.
        
        Args:
            package_name: Name of the package
            
        Returns:
            Version string if installed, None otherwise
        """
        pass

    @abstractmethod
    def install(self, package_name: str, extra_args: List[str] = None) -> bool:
        """
        Install a package.
        
        Args:
            package_name: Name of the package to install
            extra_args: Optional list of extra arguments to pass to the backend
            
        Returns:
            True if installation is successful, False otherwise
        """
        pass

    @abstractmethod
    def update(self) -> bool:
        """
        Update package lists and repositories.
        
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def upgrade(self, package_name: Optional[str] = None) -> bool:
        """
        Upgrade all packages, or a specific package if provided.
        
        Args:
            package_name: Optional package to upgrade
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def remove(self, package_name: str) -> bool:
        """
        Remove a package.
        
        Args:
            package_name: Name of the package to remove
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def list_packages(self) -> List[PackageInfo]:
        """
        List all installed packages from this backend.
        
        Returns:
            List of PackageInfo objects
        """
        pass
