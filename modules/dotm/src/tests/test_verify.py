"""Tests for dotm.verify module."""

from pathlib import Path
from unittest.mock import patch

from dotm.verify import verify_module


def _make_module(name, **kwargs):
    """Create a module dict for testing."""
    return {
        "name": name,
        "path": Path(f"/tmp/{name}"),
        "config": {},
        "homebrew_packages": kwargs.get("packages", []),
        "homebrew_casks": kwargs.get("casks", []),
        "homebrew_taps": kwargs.get("taps", []),
        "mas_installed_apps": kwargs.get("mas", []),
        "stow_dirs": kwargs.get("stow_dirs", []),
        "mergeable_files": kwargs.get("mergeable_files", []),
    }


def test_verify_packages_all_present():
    mod = _make_module("test", packages=["curl", "git"])
    with patch("dotm.verify._run", return_value={"curl", "git", "wget"}):
        checks = verify_module(mod)
    assert all(ok for _, ok, _ in checks)
    assert len(checks) == 2


def test_verify_packages_missing():
    mod = _make_module("test", packages=["curl", "missing-pkg"])
    with patch("dotm.verify._run", return_value={"curl", "git"}):
        checks = verify_module(mod)
    passed = [c for c in checks if c[1]]
    failed = [c for c in checks if not c[1]]
    assert len(passed) == 1
    assert len(failed) == 1
    assert failed[0][0] == "brew:missing-pkg"


def test_verify_casks():
    mod = _make_module("test", casks=["firefox", "slack"])
    with patch("dotm.verify._run", return_value={"firefox"}):
        checks = verify_module(mod)
    passed = [c for c in checks if c[1]]
    failed = [c for c in checks if not c[1]]
    assert len(passed) == 1
    assert len(failed) == 1


def test_verify_taps():
    mod = _make_module("test", taps=["homebrew/core", "custom/tap"])
    with patch("dotm.verify._run", return_value={"homebrew/core"}):
        checks = verify_module(mod)
    passed = [c for c in checks if c[1]]
    failed = [c for c in checks if not c[1]]
    assert len(passed) == 1
    assert len(failed) == 1


def test_verify_stow_links(tmp_path):
    """Test symlink verification."""
    # Set up dotmodules dir with a source file
    home = tmp_path / "home"
    home.mkdir()
    dotmodules = home / ".dotmodules" / "test" / "files"
    dotmodules.mkdir(parents=True)
    src_file = dotmodules / ".config" / "test.conf"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("test config")

    # Create a correct symlink
    target = home / ".config" / "test.conf"
    target.parent.mkdir(parents=True)
    target.symlink_to(src_file)

    mod = _make_module("test", stow_dirs=["test"])
    with patch("dotm.verify.Path.home", return_value=home):
        checks = verify_module(mod)
    assert any(ok for _, ok, _ in checks)


def test_verify_empty_module():
    """Module with no packages/casks/stow should produce no checks."""
    mod = _make_module("empty")
    checks = verify_module(mod)
    assert checks == []
