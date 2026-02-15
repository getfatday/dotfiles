"""Tests for dotm.modules module."""

from pathlib import Path
from unittest.mock import patch

import yaml

from dotm.modules import (
    create_module,
    list_all_modules,
    get_deploy_modules,
    is_module_installed,
)


def _create_module_dir(modules_dir: Path, name: str, config: dict) -> Path:
    """Helper to create a module directory with config.yml."""
    mod_dir = modules_dir / name
    mod_dir.mkdir(parents=True)
    (mod_dir / "config.yml").write_text(yaml.dump(config, default_flow_style=False))
    return mod_dir


def test_list_all_modules(tmp_path):
    modules_dir = tmp_path / "modules"
    _create_module_dir(modules_dir, "foo", {"homebrew_packages": ["curl"]})
    _create_module_dir(modules_dir, "bar", {"homebrew_casks": ["firefox"]})
    # Dir without config.yml should be skipped
    (modules_dir / "no-config").mkdir()

    with patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        modules = list_all_modules()

    names = [m["name"] for m in modules]
    assert "bar" in names
    assert "foo" in names
    assert "no-config" not in names
    assert len(modules) == 2


def test_list_all_modules_empty(tmp_path):
    with patch("dotm.modules.get_modules_dir", return_value=tmp_path / "nonexistent"):
        modules = list_all_modules()
    assert modules == []


def test_list_module_fields(tmp_path):
    modules_dir = tmp_path / "modules"
    _create_module_dir(modules_dir, "test", {
        "homebrew_packages": ["a", "b"],
        "homebrew_casks": ["c"],
        "homebrew_taps": ["d/e"],
        "mas_installed_apps": [123],
        "stow_dirs": ["test"],
        "mergeable_files": [".zshrc"],
    })

    with patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        modules = list_all_modules()
    mod = modules[0]
    assert mod["homebrew_packages"] == ["a", "b"]
    assert mod["homebrew_casks"] == ["c"]
    assert mod["homebrew_taps"] == ["d/e"]
    assert mod["mas_installed_apps"] == [123]
    assert mod["stow_dirs"] == ["test"]
    assert mod["mergeable_files"] == [".zshrc"]


def test_get_deploy_modules(tmp_path):
    deploy_yml = tmp_path / "playbooks" / "deploy.yml"
    deploy_yml.parent.mkdir(parents=True)
    deploy_yml.write_text(yaml.dump([{
        "name": "Deploy",
        "hosts": "localhost",
        "vars": {"dotmodules": {"install": ["git", "zsh", "node"]}},
    }]))

    with patch("dotm.modules.get_dotfiles_repo", return_value=tmp_path):
        result = get_deploy_modules()
    assert result == ["git", "zsh", "node"]


def test_is_module_installed(tmp_path):
    deploy_yml = tmp_path / "playbooks" / "deploy.yml"
    deploy_yml.parent.mkdir(parents=True)
    deploy_yml.write_text(yaml.dump([{
        "name": "Deploy",
        "hosts": "localhost",
        "vars": {"dotmodules": {"install": ["git", "zsh"]}},
    }]))

    with patch("dotm.modules.get_dotfiles_repo", return_value=tmp_path):
        assert is_module_installed("git") is True
        assert is_module_installed("missing") is False


def test_create_module(tmp_path):
    modules_dir = tmp_path / "modules"
    modules_dir.mkdir()

    with patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        mod_dir = create_module("test-pkg", homebrew_packages=["tree", "htop"])

    assert mod_dir.exists()
    config = yaml.safe_load((mod_dir / "config.yml").read_text())
    assert config["homebrew_packages"] == ["tree", "htop"]


def test_create_module_with_stow(tmp_path):
    modules_dir = tmp_path / "modules"
    modules_dir.mkdir()

    with patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        mod_dir = create_module("test-stow", homebrew_packages=["vim"], stow=True)

    assert (mod_dir / "files").is_dir()
    config = yaml.safe_load((mod_dir / "config.yml").read_text())
    assert config["stow_dirs"] == ["test-stow"]


def test_create_module_already_exists(tmp_path):
    modules_dir = tmp_path / "modules"
    (modules_dir / "existing").mkdir(parents=True)

    with patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        try:
            create_module("existing")
            assert False, "Should have raised FileExistsError"
        except FileExistsError:
            pass
