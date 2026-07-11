import sys
from upk.upk import get_configured_backends
from upk.search import list_all_backends

backends = get_configured_backends()
results = list_all_backends(backends)
for pkg in results:
    if 'miniclip' in pkg.name.lower():
        print(f"Name: '{pkg.name}', Source: {pkg.source}, Installed Version: {pkg.installed_version}, Version: {pkg.version}, is_installed: {pkg.is_installed}")
