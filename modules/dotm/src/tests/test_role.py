"""Tests for the role and `requires:` grammar: what a machine's capability set selects."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from dotm.config import DEFAULT_PLATFORM
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


# Base modules whose requirements go beyond the platform, and the machine-declared capability
# each one needs. Requirements are added one PR at a time; every addition extends this map.
OPT_IN = {"tart": ["virtualization-host"], "session-host": ["session-host"]}


def test_repo_base_modules_require_the_macos_platform_or_a_declared_capability():
    """Landing contract: a base module requires nothing, `macos`, or `macos` plus a capability
    profiles.yml lists under `declared_capabilities:` (named per module in OPT_IN). It carries
    `macos` only when every package it declares is a Homebrew cask, formula, tap or mas id. A Mac
    (the default platform) therefore resolves base_modules minus its exclusions minus the opt-in
    modules, as before; only a machine that declares a non-macOS platform drops the rest."""
    data = yaml.safe_load(PROFILES_YML.read_text())
    base = data["base_modules"]
    declared = data["declared_capabilities"]
    requiring, opt_in = [], []
    for name in base:
        config = yaml.safe_load((MODULES_DIR / name / "config.yml").read_text()) or {}
        reqs = module_requires(config, name)
        allowed = ([], ["macos"], ["macos", *OPT_IN.get(name, [])])
        assert reqs in allowed, f"{name} requires {reqs}; add requirements one PR at a time"
        if reqs:
            requiring.append(name)
            assert not config.get("apt_packages"), f"{name} requires macos but lists apt packages"
            # An opt-in module may carry no packages when its payload is a deploy.yml block gated
            # on the same capability (session-host: pmset and systemsetup need root and are not
            # package keys). Every other requiring module installs something.
            assert name in OPT_IN or any(config.get(k) for k in ("homebrew_casks", "homebrew_packages",
                                                                  "homebrew_taps", "mas_installed_apps",
                                                                  "github_releases")), \
                f"{name} requires macos for nothing"
        if name in OPT_IN:
            opt_in.append(name)
            assert reqs == ["macos", *OPT_IN[name]], f"{name} must require exactly {OPT_IN[name]}"
            for cap in OPT_IN[name]:
                assert cap in declared, f"{cap} is not listed under declared_capabilities"
    assert requiring, "expected the macOS-only modules to declare requires: [macos]"
    assert sorted(opt_in) == sorted(OPT_IN), "every OPT_IN module is a base module"
    excluded = ["docker"]
    expected = sorted(set(base) - set(excluded) - set(opt_in))
    for role in [None, *data["role_capabilities"]]:
        caps = resolve_capabilities(role, DEFAULT_PLATFORM, data["role_capabilities"])
        assert select_modules([m for m in base if m not in excluded], caps, MODULES_DIR) == expected
    # Without the platform joined, exactly the requiring modules drop: the counterfactual the
    # deploy.yml join line exists to prevent.
    assert select_modules(base, resolve_capabilities(None, [], data["role_capabilities"]), MODULES_DIR) \
        == sorted(set(base) - set(requiring))
    linux = resolve_capabilities("mixed", ["linux-arm", "apt", "headless"], data["role_capabilities"])
    assert select_modules(base, linux, MODULES_DIR) == sorted(set(base) - set(requiring))


def test_repo_tart_is_selected_only_where_virtualization_host_is_declared():
    """The VM fixture: `tart` joins base_modules requiring `virtualization-host`, which no role
    provides. A Mac that does not declare it resolves exactly the set it resolved before tart
    landed; a Mac that declares it under `capabilities:` gains tart and nothing else."""
    data = yaml.safe_load(PROFILES_YML.read_text())
    roles = data["role_capabilities"]
    base = data["base_modules"]
    assert "tart" in base
    assert module_requires(yaml.safe_load((MODULES_DIR / "tart" / "config.yml").read_text()), "tart") \
        == ["macos", "virtualization-host"]
    assert "virtualization-host" not in {c for caps in roles.values() for c in caps}
    assert "virtualization-host" in data["declared_capabilities"]
    before = sorted(set(base) - set(OPT_IN))
    for role in [None, *roles]:
        without = select_modules(base, resolve_capabilities(role, DEFAULT_PLATFORM, roles), MODULES_DIR)
        assert "tart" not in without
        assert without == before, f"role {role}: a machine without the capability changed"
        assert len(without) == len(base) - len(OPT_IN)
        with_cap = select_modules(base, resolve_capabilities(role, [*DEFAULT_PLATFORM, "virtualization-host"],
                                                             roles), MODULES_DIR)
        assert with_cap == sorted(before + ["tart"]), f"role {role}: declaring the capability should add exactly tart"
    # The capability alone is not enough off macOS: Tart is Apple Virtualization.
    pi = resolve_capabilities("personal", ["linux-arm", "apt", "headless", "virtualization-host"], roles)
    assert "tart" not in select_modules(base, pi, MODULES_DIR)


def test_declared_capabilities_never_count_as_unprovided(tmp_path):
    modules_dir = _tree(tmp_path)
    _module(modules_dir, "vm-runner", {"homebrew_packages": ["vm"], "requires": ["macos", "virtualization-host"]})
    _module(modules_dir, "orphan", {"requires": ["nothing-provides-this"]})
    with patch("dotm.modules.get_role_capabilities", return_value=ROLES), \
         patch("dotm.modules.get_declared_capability_names", return_value=["virtualization-host"]), \
         patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        assert unprovided_requirements() == {"orphan": ["nothing-provides-this"]}
    with patch("dotm.modules.get_role_capabilities", return_value=ROLES), \
         patch("dotm.modules.get_declared_capability_names", return_value=[]), \
         patch("dotm.modules.get_modules_dir", return_value=modules_dir):
        assert unprovided_requirements()["vm-runner"] == ["virtualization-host"]


def test_repo_session_host_is_selected_only_where_the_capability_is_declared():
    """The remote session host: `session-host` joins base_modules requiring the capability of the
    same name, which no role provides. A Mac that does not declare it resolves exactly the set it
    resolved before this module landed; a Mac that declares it under `capabilities:` gains
    session-host and nothing else. The deploy.yml post_tasks that set the power and Remote Login
    state are gated on the same capability string, so the two halves cannot drift apart."""
    data = yaml.safe_load(PROFILES_YML.read_text())
    roles = data["role_capabilities"]
    base = data["base_modules"]
    assert "session-host" in base
    config = yaml.safe_load((MODULES_DIR / "session-host" / "config.yml").read_text())
    assert module_requires(config, "session-host") == ["macos", "session-host"]
    assert "session-host" not in {c for caps in roles.values() for c in caps}
    assert "session-host" in data["declared_capabilities"]
    deploy = (PROFILES_YML.parent / "deploy.yml").read_text()
    assert deploy.count("'session-host' in dotm_capabilities") >= 4
    before = sorted(set(base) - set(OPT_IN))
    for role in [None, *roles]:
        without = select_modules(base, resolve_capabilities(role, DEFAULT_PLATFORM, roles), MODULES_DIR)
        assert "session-host" not in without
        assert without == before, f"role {role}: a machine without the capability changed"
        assert len(without) == len(base) - len(OPT_IN)
        with_cap = select_modules(base, resolve_capabilities(role, [*DEFAULT_PLATFORM, "session-host"], roles),
                                  MODULES_DIR)
        assert with_cap == sorted(before + ["session-host"]), \
            f"role {role}: declaring the capability should add exactly session-host"
    # Off macOS the capability alone selects nothing: pmset and systemsetup are macOS tools.
    pi = resolve_capabilities("personal", ["linux-arm", "apt", "headless", "session-host"], roles)
    assert "session-host" not in select_modules(base, pi, MODULES_DIR)
