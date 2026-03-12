# UPK DEB Packaging Guide

This guide explains how to build a DEB package for UPK (Ubuntu Package Kit) using PyInstaller to create a standalone executable.

## Overview

The packaging process creates a Python package and packages it into a DEB file that can be installed on Ubuntu/Debian systems. This approach has several advantages:

- **Small package size**: Only includes source code and metadata (~30KB)
- **System integration**: Uses system Python and dependencies
- **Easy installation**: Users can install with `sudo dpkg -i upk-{version}.deb`
- **CLI-optimized**: No desktop integration (suitable for command-line tools)
- **Maintainable**: Standard Python package structure

## Prerequisites

- Python 3.10 or higher
- pip
- dpkg-deb (usually pre-installed on Ubuntu/Debian)

## Building the DEB Package

### Quick Start

1. Make the build script executable:
   ```bash
   chmod +x build.sh
   ```

2. Run the build script:
   ```bash
   ./build.sh
   ```

3. Install the package:
   ```bash
   sudo dpkg -i upk-{version}.deb
   ```

### What the Build Script Does

1. **Copies source files** to the proper Python package structure
2. **Creates a wrapper script** that executes the Python module
3. **Creates the DEB package structure** with proper directory layout
4. **Generates package metadata** including control file and documentation
5. **Builds the final DEB package** using dpkg-deb

## Package Contents

The resulting DEB package includes:

- **Executable**: `/usr/bin/upk` - The main UPK application
- **Shell Completion**: `/usr/share/bash-completion/completions/upk` - Automatic Bash autocomplete
- **Managed AppImages**: Stored in the location defined by `path_appimages` (default `~/.local/share/applications/AppImages`)
- **Documentation**: `/usr/share/doc/upk/` - Package documentation and license
- **Post-installation script**: Handles setup tasks after installation

## Package Dependencies

### Runtime Dependencies
- `python3 (>= 3.10)` - Python interpreter (for compatibility)
- `python3-click (>= 8.1.0)` - Command-line interface library
- `python3-rich (>= 13.0.0)` - Rich text formatting library

### Recommended Packages
- `apt` - APT package manager
- `snapd` - Snap package manager
- `flatpak` - Flatpak package manager
- `pacstall` - Pacstall package manager
- `am` - AppMan package manager

## Installation

### Install the Package
```bash
sudo dpkg -i upk-{version}.deb
```

### Fix Missing Dependencies (if needed)
```bash
sudo apt install -f
```

### Verify Installation
```bash
upk --help
```


## Uninstallation

```bash
sudo dpkg -r upk
```

## Package Structure

```
upk-debian/
├── DEBIAN/
│   ├── control          # Package metadata
│   ├── postinst         # Post-installation script
│   └── postrm          # Post-removal script
├── usr/
│   ├── bin/
│   │   └── upk         # Main executable
│   └── share/
│       └── doc/
│           └── upk/    # Documentation
│               ├── changelog.Debian
│               ├── copyright
│               └── README.Debian
```

## Troubleshooting

### Build Script Issues

**PyInstaller not found**: The script automatically creates a virtual environment and installs PyInstaller.

**Missing dependencies**: The script installs click and rich dependencies in the virtual environment.

**Permission errors**: Ensure you're not running as root during the build process.

### Installation Issues

**Missing dependencies**: Run `sudo apt install -f` to install missing dependencies.

**Architecture mismatch**: The package is built for amd64 architecture. For other architectures, you'll need to build on the target system.

### Runtime Issues

**Executable not found**: Ensure the package was installed correctly with `which upk`.

**Missing system tools**: Install recommended packages for full functionality:
```bash
sudo apt install apt snapd flatpak pacstall
```

## Customization

### Package Metadata

Edit the following in `build.sh`:

- **Maintainer information**: Update the maintainer name and email in the control file
- **Package version**: Modify the version number
- **Description**: Update the package description
- **Dependencies**: Adjust dependencies based on your requirements

### Build Configuration

- **PyInstaller options**: Modify PyInstaller flags in the build command
- **Included files**: Update the `--add-data` flags to include additional files
- **Package structure**: Modify the directory structure as needed

## Development

### Testing the Build Process

1. Clean previous builds:
   ```bash
   rm -f upk-{version}.deb dist/upk build/ -rf
   ```

2. Rebuild:
   ```bash
   ./build.sh
   ```

3. Test installation in a clean environment or virtual machine

### Debugging

- **PyInstaller warnings**: Check the build output for any warnings
- **Package contents**: Use `dpkg-deb --contents upk-{version}.deb` to verify contents
- **Installation logs**: Check system logs during installation

## Security Considerations

- The executable is self-contained and doesn't require additional Python packages
- The post-installation script runs with root privileges during installation
- All dependencies are bundled, reducing attack surface from external packages

## Performance

- **Package size**: ~30KB (source code only)
- **Startup time**: Standard Python startup time
- **Memory usage**: Standard Python memory usage
- **Dependencies**: Uses system-installed packages

## Support

For issues with the DEB package:

1. Check the troubleshooting section above
2. Verify your system meets the requirements
3. Test with a clean installation
4. Report issues with build output and system information

## License

The DEB packaging scripts and documentation are provided under the same license as the main UPK project.