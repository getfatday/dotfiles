"""Tests for dotm.analyze module."""

from unittest.mock import patch

from dotm.analyze import (
    analyze_brew,
    analyze_cask,
    analyze_mas,
    get_managed_packages,
    get_managed_casks,
)


def _mock_modules(packages=None, casks=None, mas=None):
    """Create mock module list."""
    return [{
        "name": "test",
        "path": "/tmp/test",
        "config": {},
        "homebrew_packages": packages or [],
        "homebrew_casks": casks or [],
        "homebrew_taps": [],
        "mas_installed_apps": mas or [],
        "stow_dirs": [],
        "mergeable_files": [],
    }]


def test_get_managed_packages():
    mods = _mock_modules(packages=["curl", "wget"])
    with patch("dotm.analyze.list_all_modules", return_value=mods):
        assert get_managed_packages() == {"curl", "wget"}


def test_get_managed_casks():
    mods = _mock_modules(casks=["firefox", "chrome"])
    with patch("dotm.analyze.list_all_modules", return_value=mods):
        assert get_managed_casks() == {"firefox", "chrome"}


def test_analyze_brew_with_mock():
    mods = _mock_modules(packages=["curl", "git"])
    with patch("dotm.analyze.list_all_modules", return_value=mods), \
         patch("dotm.analyze._run", return_value=["curl", "git", "wget", "jq"]):
        result = analyze_brew()
    assert result["installed"] == 4
    assert result["managed"] == 2
    assert sorted(result["unmanaged"]) == ["jq", "wget"]


def test_analyze_brew_all_managed():
    mods = _mock_modules(packages=["curl", "git"])
    with patch("dotm.analyze.list_all_modules", return_value=mods), \
         patch("dotm.analyze._run", return_value=["curl", "git"]):
        result = analyze_brew()
    assert result["unmanaged"] == []


def test_analyze_cask_with_mock():
    mods = _mock_modules(casks=["firefox"])
    with patch("dotm.analyze.list_all_modules", return_value=mods), \
         patch("dotm.analyze._run", return_value=["firefox", "slack", "zoom"]):
        result = analyze_cask()
    assert result["installed"] == 3
    assert result["managed"] == 1
    assert sorted(result["unmanaged"]) == ["slack", "zoom"]


def test_analyze_mas_with_mock():
    mods = _mock_modules(mas=[123])
    with patch("dotm.analyze.list_all_modules", return_value=mods), \
         patch("dotm.analyze._run", return_value=["123 MyApp (1.0)", "456 OtherApp (2.0)"]):
        result = analyze_mas()
    assert result["installed"] == 2
    assert result["managed"] == 1
    assert 456 in result["unmanaged"]
    assert 123 not in result["unmanaged"]


def test_analyze_brew_command_fails():
    mods = _mock_modules(packages=["curl"])
    with patch("dotm.analyze.list_all_modules", return_value=mods), \
         patch("dotm.analyze._run", return_value=[]):
        result = analyze_brew()
    assert result["installed"] == 0
    assert result["unmanaged"] == []
