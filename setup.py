#!/usr/bin/env python3
"""Setup script for UPK - Ubuntu Package Kit."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements from pyproject.toml
def get_requirements():
    """Extract dependencies from pyproject.toml."""
    import tomllib
    pyproject_path = this_directory / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        return pyproject_data.get("project", {}).get("dependencies", [])
    return []

setup(
    name="upk",
    version="0.1.0",
    description="Ubuntu Package Kit - Universal package manager wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/upk",
    packages=find_packages(),
    include_package_data=True,
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "upk=upk:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Software Distribution",
        "Topic :: Utilities",
    ],
    python_requires=">=3.10",
    keywords="package manager apt snap flatpak pacstall appimage",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/upk/issues",
        "Source": "https://github.com/yourusername/upk",
    },
)