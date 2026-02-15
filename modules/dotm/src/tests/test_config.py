"""Tests for dotm.config module."""

from pathlib import Path
from unittest.mock import patch

import yaml

from dotm.config import (
    DEFAULT_CONFIG,
    ensure_config,
    exclude_module,
    get_excluded_modules,
    include_module,
    load_config,
    save_config,
)


def test_load_config_defaults(tmp_path):
    """load_config returns defaults when file doesn't exist."""
    with patch("dotm.config.CONFIG_FILE", tmp_path / "nonexistent.yml"):
        config = load_config()
    assert config["dotfiles_repo"] == "~/src/dotfiles"
    assert config["excluded_modules"] == []
    assert config["sync"]["interval_minutes"] == 30


def test_save_and_load_roundtrip(tmp_path):
    config_file = tmp_path / "config.yml"
    with patch("dotm.config.CONFIG_FILE", config_file), \
         patch("dotm.config.CONFIG_DIR", tmp_path):
        save_config({"dotfiles_repo": "~/custom", "excluded_modules": ["foo"]})
        config = load_config()
    assert config["dotfiles_repo"] == "~/custom"
    assert config["excluded_modules"] == ["foo"]


def test_ensure_config_creates_file(tmp_path):
    config_file = tmp_path / "config.yml"
    log_dir = tmp_path / "logs"
    with patch("dotm.config.CONFIG_FILE", config_file), \
         patch("dotm.config.CONFIG_DIR", tmp_path), \
         patch("dotm.config.LOG_DIR", log_dir):
        config = ensure_config()
    assert config_file.exists()
    assert log_dir.exists()
    assert config["dotfiles_repo"] == DEFAULT_CONFIG["dotfiles_repo"]


def test_exclude_module(tmp_path):
    config_file = tmp_path / "config.yml"
    config_file.write_text(yaml.dump(DEFAULT_CONFIG))
    with patch("dotm.config.CONFIG_FILE", config_file), \
         patch("dotm.config.CONFIG_DIR", tmp_path):
        exclude_module("test-mod")
        assert "test-mod" in get_excluded_modules()
        # Exclude again — should not duplicate
        exclude_module("test-mod")
        assert get_excluded_modules().count("test-mod") == 1


def test_include_module(tmp_path):
    config_file = tmp_path / "config.yml"
    config_file.write_text(yaml.dump({**DEFAULT_CONFIG, "excluded_modules": ["test-mod"]}))
    with patch("dotm.config.CONFIG_FILE", config_file), \
         patch("dotm.config.CONFIG_DIR", tmp_path):
        include_module("test-mod")
        assert "test-mod" not in get_excluded_modules()
        # Include non-excluded module — should not error
        include_module("other")
