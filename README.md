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

- 🔍 **Search packages** across all configured backends
- ⬇️ **Install packages** with source selection
- 🔄 **Update package lists** and upgrade packages
- 🗑️ **Remove packages** with automatic source detection
- ⚙️ **Configuration system** for customizing behavior
- 📋 **List installed packages** with filtering options


## Available Backends

| Backend    | Command Required    | Enabled by Default | Notes |
|------------|---------------------|-------------------|-------|
| APT        | `apt` or `nala`     | Yes               | Uses Nala if available |
| Snap       | `snap`              | Yes               | Canonical's package system |
| Flatpak    | `flatpak`           | Yes               | Cross-distro package format |
| Pacstall   | `pacstall`          | Yes               | AUR-like package manager |
| AppImage   | N/A                 | Yes               | Portable application format |

**Note**: Backends are automatically disabled if their required command isn't found.

## Installation

### Prerequisites
- Python 3.10+
- Ubuntu-based system
- Recommended: [Nala](https://gitlab.com/volian/nala) (`sudo apt install nala`)

### Install UPK
```bash
git clone https://github.com/undefinederror/upk
cd upk
pip install -e .
# optional but recommended
# add an alias in your ~/.bash_aliases
alias upk='python3 /path/to/upk/upk.py'

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

# List all configurations
upk config list
```

## Usage Examples

```bash
# Search for packages
upk search firefox

# Search for packages, exact match
upk search firefox -e

# Install Firefox, follow prompt and choose source
upk install firefox

# Install Firefox via specific backend
upk install firefox --source flatpak

# Update package lists
upk update

# Upgrade all packages
upk upgrade

# Upgrade a specific package
upk upgrade firefox

# Remove package
upk remove firefox

# List installed packages
upk list
```


## License

MIT License - see [LICENSE](LICENSE) for details.