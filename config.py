import json
import os
from pathlib import Path
from typing import Dict, Any, List

CONFIG_DIR = Path.home() / ".config" / "upk"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "backends_priority": ["apt", "flatpak", "snap", "pacstall"],
    "disabled_backends": [],
    "always_exact_search": False,
    "interactive_prompts": True,
    "path_downloads": "~/.local/share/upk/downloads",
    "path_appimages": "~/.local/share/applications/AppImages",
}

def load_config() -> Dict[str, Any]:
    """Load configuration from disk, creating defaults if necessary."""
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
        
    try:
        with open(CONFIG_FILE, 'r') as f:
            user_config = json.load(f)
            
        # Merge with defaults to ensure all keys exist
        config = DEFAULT_CONFIG.copy()
        config.update(user_config)
        return config
    except Exception as e:
        print(f"Warning: Failed to load config ({e}). Using defaults.")
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Warning: Failed to save config ({e}).")

def get_value(key: str) -> Any:
    """Get a specific configuration value."""
    config = load_config()
    return config.get(key, DEFAULT_CONFIG.get(key))

def set_value(key: str, value: Any) -> bool:
    """Set a specific configuration value."""
    if key not in DEFAULT_CONFIG:
        return False
        
    config = load_config()
    config[key] = value
    save_config(config)
    return True
