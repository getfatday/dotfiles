"""Local configuration management for dotm."""

from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    "dotfiles_repo": "~/src/dotfiles",
    "excluded_modules": [],
    "sync": {
        "interval_minutes": 30,
        "auto_apply": True,
    },
}

CONFIG_DIR = Path.home() / ".config" / "dotm"
CONFIG_FILE = CONFIG_DIR / "config.yml"
LOG_DIR = CONFIG_DIR / "logs"


def ensure_config() -> dict:
    """Create default config if it doesn't exist, then return it."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(yaml.dump(DEFAULT_CONFIG, default_flow_style=False, sort_keys=False))

    return load_config()


def load_config() -> dict:
    """Load the local dotm config."""
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_CONFIG)
    with open(CONFIG_FILE) as f:
        data = yaml.safe_load(f) or {}
    # Merge defaults for any missing keys
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    return merged


def save_config(config: dict) -> None:
    """Write the local dotm config."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def get_dotfiles_repo() -> Path:
    """Return the resolved path to the dotfiles repo."""
    config = load_config()
    return Path(config["dotfiles_repo"]).expanduser()


def get_modules_dir() -> Path:
    """Return the path to the modules directory."""
    return get_dotfiles_repo() / "modules"


def get_excluded_modules() -> list[str]:
    """Return the list of excluded module names."""
    config = load_config()
    return config.get("excluded_modules", [])


def exclude_module(name: str) -> None:
    """Add a module to the exclusion list."""
    config = load_config()
    excluded = config.get("excluded_modules", [])
    if name not in excluded:
        excluded.append(name)
        config["excluded_modules"] = excluded
        save_config(config)


def include_module(name: str) -> None:
    """Remove a module from the exclusion list."""
    config = load_config()
    excluded = config.get("excluded_modules", [])
    if name in excluded:
        excluded.remove(name)
        config["excluded_modules"] = excluded
        save_config(config)
