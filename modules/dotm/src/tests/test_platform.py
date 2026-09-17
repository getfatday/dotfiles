"""Tests for the platform capability and the per-manager package resolution it gates."""

import json
from pathlib import Path
from unittest.mock import patch

import yaml

from dotm.config import DEFAULT_PLATFORM
from dotm.modules import (
    PLATFORM_CAPABILITIES,
    PLATFORM_PACKAGE_KEYS,
    list_all_modules,
    main,
    resolve_packages,
    unprovided_requirements,
)

MODULES_DIR = Path(__file__).resolve().parents[4] / "modules"
LINUX_ARM = ["linux-arm", "apt", "headless"]
HOMEBREW_KEYS = ("homebrew_taps", "homebrew_packages", "homebrew_casks", "mas_installed_apps")


def _real_modules() -> dict:
    with patch("dotm.modules.get_modules_dir", return_value=MODULES_DIR):
        return {m["name"]: m for m in list_all_modules()}


def _module(modules_dir: Path, name: str, config: dict) -> None:
    mod_dir = modules_dir / name
    mod_dir.mkdir(parents=True)
    (mod_dir / "config.yml").write_text(yaml.dump(config, default_flow_style=False))


def test_each_package_key_is_unlocked_by_exactly_one_platform_capability():
    # `github_releases` installs from a pinned release and needs no package manager, so every
    # platform capability unlocks it; every other key stays under exactly one capability.
    caps_by_key: dict[str, set] = {}
    for cap, keys in PLATFORM_PACKAGE_KEYS.items():
        for key in keys:
            caps_by_key.setdefault(key, set()).add(cap)
    assert caps_by_key["github_releases"] == set(PLATFORM_PACKAGE_KEYS)
    assert all(len(caps) == 1 for key, caps in caps_by_key.items() if key != "github_releases")
    assert set(PLATFORM_PACKAGE_KEYS) <= PLATFORM_CAPABILITIES
    assert set(DEFAULT_PLATFORM) <= PLATFORM_CAPABILITIES


def test_macos_default_reads_only_homebrew_and_mas_keys(tmp_path):
    modules_dir = tmp_path / "modules"
    _module(modules_dir, "a", {"homebrew_packages": ["x"], "homebrew_taps": ["t/t"],
                               "apt_packages": ["x-apt"]})
    _module(modules_dir, "b", {"homebrew_casks": ["c"], "mas_installed_apps": [7], "apt_packages": ["y"]})
    with patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        resolved = resolve_packages(list_all_modules(), DEFAULT_PLATFORM)
    assert resolved == {"homebrew_taps": ["t/t"], "homebrew_packages": ["x"],
                        "homebrew_casks": ["c"], "mas_installed_apps": [7], "github_releases": []}
    assert "apt_packages" not in resolved


def test_linux_arm_reads_only_the_apt_key_and_reports_modules_that_contribute_nothing(tmp_path):
    modules_dir = tmp_path / "modules"
    _module(modules_dir, "a", {"homebrew_packages": ["x"], "apt_packages": ["x-apt", "a-apt"]})
    _module(modules_dir, "only-brew", {"homebrew_casks": ["c"]})
    lines = []
    with patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        resolved = resolve_packages(list_all_modules(), LINUX_ARM, report=lines.append)
    assert resolved == {"apt_packages": ["a-apt", "x-apt"], "github_releases": []}
    assert lines == ["resolve: module 'only-brew' contributes no packages for platform [linux-arm, apt, headless]"]


def test_list_all_modules_exposes_apt_packages(tmp_path):
    modules_dir = tmp_path / "modules"
    _module(modules_dir, "a", {"apt_packages": ["p"]})
    _module(modules_dir, "b", {"homebrew_packages": ["q"]})
    with patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        by_name = {m["name"]: m for m in list_all_modules()}
    assert by_name["a"]["apt_packages"] == ["p"]
    assert by_name["b"]["apt_packages"] == []


def test_platform_capabilities_never_count_as_unprovided(tmp_path):
    modules_dir = tmp_path / "modules"
    _module(modules_dir, "mac-only", {"homebrew_casks": ["c"], "requires": ["macos"]})
    _module(modules_dir, "pi-only", {"apt_packages": ["p"], "requires": ["linux-arm", "apt"]})
    _module(modules_dir, "orphan", {"requires": ["nothing-provides-this"]})
    with patch("dotm.modules.get_role_capabilities", return_value={"work": ["work-login"]}), \
         patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        assert unprovided_requirements() == {"orphan": ["nothing-provides-this"]}


def test_repo_git_zsh_tmux_resolve_to_apt_lists_on_linux_arm():
    by_name = _real_modules()
    expected = {"git": ["gh", "git", "git-delta", "git-filter-repo", "git-flow"], "zsh": ["zsh"], "tmux": ["tmux"]}
    for name, apt in expected.items():
        resolved = resolve_packages([by_name[name]], LINUX_ARM)
        assert resolved == {"apt_packages": apt, "github_releases": []}, name


def test_repo_homebrew_only_module_resolves_to_an_empty_linux_arm_set_with_one_report_line():
    by_name = _real_modules()
    bun = by_name["bun"]
    assert bun["requires"] == [] and bun["apt_packages"] == []
    assert any(bun[k] for k in HOMEBREW_KEYS)
    lines = []
    assert resolve_packages([bun], LINUX_ARM, report=lines.append) == {"apt_packages": [],
                                                                      "github_releases": []}
    assert lines == ["resolve: module 'bun' contributes no packages for platform [linux-arm, apt, headless]"]


def test_repo_linux_arm_resolution_carries_no_homebrew_item():
    by_name = _real_modules()
    resolved = resolve_packages(list(by_name.values()), LINUX_ARM)
    assert list(resolved) == ["apt_packages", "github_releases"]
    assert resolved["apt_packages"]
    casks_taps_mas = {str(i) for m in by_name.values()
                      for k in ("homebrew_casks", "homebrew_taps", "mas_installed_apps") for i in m[k]}
    assert not casks_taps_mas & set(resolved["apt_packages"])


def test_resolve_entry_prints_json_for_named_modules(capsys):
    with patch("dotm.modules.get_modules_dir", return_value=MODULES_DIR):
        rc = main(["resolve", "--platform", "linux-arm,apt,headless", "--modules", "zsh,bun"])
    out, err = capsys.readouterr()
    assert rc == 0
    assert json.loads(out) == {"apt_packages": ["zsh"], "github_releases": []}
    assert err.strip() == "resolve: module 'bun' contributes no packages for platform [linux-arm, apt, headless]"
    with patch("dotm.modules.get_modules_dir", return_value=MODULES_DIR):
        assert main(["resolve", "--platform", "apt", "--modules", "no-such-module"]) == 2
