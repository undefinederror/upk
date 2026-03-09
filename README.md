# UPK - Ubuntu Package Kit

A unified CLI for managing packages across multiple package managers on Ubuntu systems. Shamelessly inspired by [rpk from Rhino Linux](https://github.com/rhino-linux/rpk).

```
>> upk install firefox -e
Searching for firefox across available sources...

┏━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Package Name ┃ Version           ┃ Source ┃ Installed           ┃
┡━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ firefox      │ 1:1snap1-0ubuntu7 │ apt    │ 1:1snap1-0ubuntu7 ✓ │
│ 2 │ firefox      │ 147.0.4-1         │ snap   │ 147.0.4-1 ✓         │
└───┴──────────────┴───────────────────┴────────┴─────────────────────┘

Found 2 package(s)
Enter the number of the package to install (or 'q' to cancel): 
```

## Features

- 🔍 **Search packages** across all configured backends with live progress
- ⬇️ **Install packages** with interactive source selection
- 📦 **Install local files** - supports `.deb` and `.AppImage` files
- 🌐 **Install remote files** - download and install from URLs
- 🔄 **Update package lists** and upgrade packages
- 🗑️ **Remove packages** with automatic source detection
- 📋 **List installed packages** with filtering options
- ⚙️ **Configuration system** for customizing behavior
- 🎯 **Exact match searching** to find specific packages

## Available Backends

| Backend    | Command Required    | Enabled by Default | Notes |
|------------|---------------------|-------------------|-------|
| APT        | `apt` or `nala`     | Yes               | Uses Nala if available |
| Snap       | `snap`              | Yes               | Canonical's package system |
| Flatpak    | `flatpak`           | Yes               | Cross-distro package format |
| Pacstall   | `pacstall`          | Yes               | AUR-like package manager |
| AppImage   | `am`                | Yes               | [Application Manager](https://github.com/ivan-hc/AM) by ivan-hc |

**Note**: Backends are automatically disabled if their required command isn't found.

## Installation

### Prerequisites
- Python 3.10+
- Ubuntu-based system
- Optional: [Nala](https://gitlab.com/volian/nala) (`sudo apt install nala`) for faster APT operations

### Install UPK
Grab the .deb file from [releases](https://github.com/undefinederror/upk/releases)
```

## Configuration

Configure preferences via `upk config`:
```bash
# Set backend priority
upk config set backends_priority '["apt", "flatpak", "pacstall"]'

# Disable Snap backend
upk config set disabled_backends '["snap"]'

# Enable exact match searching
upk config set always_exact_search true

# Disable interactive prompts
upk config set interactive_prompts false

# List all configurations
upk config list

# Get a specific config value
upk config get backends_priority
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `backends_priority` | list | `["apt", "flatpak", "snap", "pacstall"]` | Order to prioritize backends in search results |
| `disabled_backends` | list | `[]` | List of backends to disable |
| `always_exact_search` | bool | `false` | Only show exact matches in search |
| `interactive_prompts` | bool | `true` | Enable interactive prompts for package selection |
| `path_downloads` | string | `~/.local/share/upk/downloads` | Directory for downloaded files |
| `path_appimages` | string | `~/.local/share/applications/AppImages` | Directory for AppImages |

## Usage Examples

```bash
# Search for packages
upk search firefox

# Search for packages, exact match only
upk search firefox -e

# Install Firefox (prompts to choose source)
upk install firefox

# Install Firefox, exact match only
upk install firefox -e

# Install Firefox with extra args for backend (e.g., --classic for snap)
# Use -- to separate extra_args from options
upk install firefox -- --classic

# Install a local .deb file
upk install ./my-package.deb

# Install a local .AppImage file
upk install ./my-app.AppImage

# Install a remote file from URL
upk install https://example.com/my-app.AppImage

# Update package lists
upk update

# Upgrade all packages
upk upgrade

# Upgrade a specific package
upk upgrade firefox

# Remove package
upk remove firefox

# List all installed packages
upk list

# List installed packages with filter
upk list firefox

# List installed packages, exact match
upk list firefox -e
```

## License

MIT License - see [LICENSE](LICENSE) for details.
