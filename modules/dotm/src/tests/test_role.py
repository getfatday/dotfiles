"""Tests for the role and `requires:` grammar: what a machine's capability set selects."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from dotm.modules import (
    create_module,
    list_all_modules,
    module_requires,
    resolve_capabilities,
    select_modules,
    unprovided_requirements,
)

PROFILES_YML = Path(__file__).resolve().parents[4] / "playbooks" / "profiles.yml"
MODULES_DIR = Path(__file__).resolve().parents[4] / "modules"

ROLES = {"work": ["work-login"], "personal": ["personal-account"],
         "mixed": ["work-login", "personal-account"]}


def _module(modules_dir: Path, name: str, config: dict) -> None:
    mod_dir = modules_dir / name
    mod_dir.mkdir(parents=True)
    (mod_dir / "config.yml").write_text(yaml.dump(config, default_flow_style=False))


def _tree(tmp_path: Path) -> Path:
    """A synthetic module tree: two modules that require nothing, one per role capability."""
    modules_dir = tmp_path / "modules"
    _module(modules_dir, "git", {"homebrew_packages": ["git"]})
    _module(modules_dir, "zsh", {"stow_dirs": ["zsh"]})
    _module(modules_dir, "home-ledger", {"stow_dirs": ["home-ledger"], "requires": ["personal-account"]})
    _module(modules_dir, "office-db", {"homebrew_casks": ["office-db"], "requires": ["work-login"]})
    return modules_dir


BASE = ["office-db", "zsh", "home-ledger", "git"]


def test_no_role_selects_base_modules_minus_exclusions_when_nothing_requires(tmp_path):
    """The live shape today: no role, no module with `requires:`."""
    modules_dir = tmp_path / "modules"
    _module(modules_dir, "git", {"homebrew_packages": ["git"]})
    _module(modules_dir, "zsh", {"stow_dirs": ["zsh"]})
    _module(modules_dir, "node", {"homebrew_packages": ["node"]})
    caps = resolve_capabilities(None, [], ROLES)
    assert caps == set()
    candidates = [m for m in ["zsh", "node", "git"] if m not in ["node"]]
    assert select_modules(candidates, caps, modules_dir) == ["git", "zsh"]


def test_no_role_omits_every_module_that_requires_something(tmp_path):
    modules_dir = _tree(tmp_path)
    assert select_modules(BASE, resolve_capabilities(None, [], ROLES), modules_dir) == ["git", "zsh"]


def test_role_personal_includes_personal_account_module_and_omits_work(tmp_path):
    modules_dir = _tree(tmp_path)
    caps = resolve_capabilities("personal", [], ROLES)
    assert caps == {"personal-account"}
    assert select_modules(BASE, caps, modules_dir) == ["git", "home-ledger", "zsh"]


def test_role_work_includes_work_login_module_and_omits_personal(tmp_path):
    modules_dir = _tree(tmp_path)
    caps = resolve_capabilities("work", [], ROLES)
    assert select_modules(BASE, caps, modules_dir) == ["git", "office-db", "zsh"]


def test_role_mixed_is_the_union(tmp_path):
    modules_dir = _tree(tmp_path)
    personal = select_modules(BASE, resolve_capabilities("personal", [], ROLES), modules_dir)
    work = select_modules(BASE, resolve_capabilities("work", [], ROLES), modules_dir)
    mixed = select_modules(BASE, resolve_capabilities("mixed", [], ROLES), modules_dir)
    assert mixed == sorted(set(personal) | set(work))
    assert mixed == ["git", "home-ledger", "office-db", "zsh"]


def test_declared_capabilities_join_the_role_set(tmp_path):
    """Room for a platform capability: declared directly, not through the role."""
    modules_dir = _tree(tmp_path)
    _module(modules_dir, "pi-tools", {"requires": ["linux-arm"]})
    _module(modules_dir, "mac-tools", {"requires": ["macos"]})
    caps = resolve_capabilities("personal", ["linux-arm"], ROLES)
    assert caps == {"personal-account", "linux-arm"}
    selected = select_modules(BASE + ["pi-tools", "mac-tools"], caps, modules_dir)
    assert selected == ["git", "home-ledger", "pi-tools", "zsh"]
    # A module needing two capabilities needs both.
    _module(modules_dir, "both", {"requires": ["linux-arm", "work-login"]})
    assert "both" not in select_modules(["both"], caps, modules_dir)
    assert select_modules(["both"], resolve_capabilities("mixed", ["linux-arm"], ROLES), modules_dir) == ["both"]


def test_undefined_role_is_refused():
    with pytest.raises(ValueError, match="not defined under role_capabilities"):
        resolve_capabilities("lab", [], ROLES)


def test_module_requires_validates_shape():
    assert module_requires({}, "x") == []
    assert module_requires({"requires": ["a-1", "b"]}, "x") == ["a-1", "b"]
    for bad in ("work-login", ["Work"], [1], {"a": 1}, ["with space"]):
        with pytest.raises(ValueError):
            module_requires({"requires": bad}, "x")


def test_list_all_modules_exposes_requires(tmp_path):
    modules_dir = _tree(tmp_path)
    with patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        by_name = {m["name"]: m for m in list_all_modules()}
    assert by_name["git"]["requires"] == []
    assert by_name["office-db"]["requires"] == ["work-login"]


def test_create_module_writes_requires(tmp_path):
    modules_dir = tmp_path / "modules"
    modules_dir.mkdir()
    with patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        mod_dir = create_module("needs-work", homebrew_packages=["x"], requires=["work-login"])
        plain = create_module("plain", homebrew_packages=["y"])
    assert yaml.safe_load((mod_dir / "config.yml").read_text())["requires"] == ["work-login"]
    assert "requires" not in yaml.safe_load((plain / "config.yml").read_text())


def test_unprovided_requirements_names_gaps(tmp_path):
    modules_dir = _tree(tmp_path)
    _module(modules_dir, "orphan", {"requires": ["nothing-provides-this"]})
    with patch("dotm.modules.get_role_capabilities", return_value=ROLES), \
         patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        assert unprovided_requirements() == {"orphan": ["nothing-provides-this"]}


def test_repo_profiles_define_the_three_roles_and_mixed_is_the_union():
    data = yaml.safe_load(PROFILES_YML.read_text())
    roles = data["role_capabilities"]
    assert set(roles) == {"work", "personal", "mixed"}
    assert set(roles["mixed"]) == set(roles["work"]) | set(roles["personal"])
    assert isinstance(data["base_modules"], list)


def test_repo_has_no_module_with_requires_yet_so_every_machine_gets_base_modules():
    """Landing contract: the grammar arrives with no module requiring anything, so a machine
    with no role resolves exactly base_modules minus its exclusions, as before."""
    data = yaml.safe_load(PROFILES_YML.read_text())
    base = data["base_modules"]
    for name in base:
        config = yaml.safe_load((MODULES_DIR / name / "config.yml").read_text()) or {}
        assert "requires" not in config, f"{name} carries requires; add requirements one PR at a time"
    caps = resolve_capabilities(None, [], data["role_capabilities"])
    assert caps == set()
    excluded = ["docker"]
    expected = sorted(set(base) - set(excluded))
    assert select_modules([m for m in base if m not in excluded], caps, MODULES_DIR) == expected
    for role in data["role_capabilities"]:
        assert select_modules(base, resolve_capabilities(role, [], data["role_capabilities"]), MODULES_DIR) == sorted(set(base))
