"""Tests for dotm.sync: deploy.yml, not dotm, resolves which modules apply."""

import json
import re
from pathlib import Path
from unittest.mock import patch

from dotm import sync as sync_mod
from dotm.config import DEFAULT_PLATFORM

DEPLOY_YML = Path(__file__).resolve().parents[4] / "playbooks" / "deploy.yml"


class _FakeProc:
    pid = 4242
    returncode = 0

    def communicate(self, timeout=None):
        return (b"", b"")


def _run_apply(tmp_path, excluded, platform=DEFAULT_PLATFORM):
    (tmp_path / "playbooks").mkdir()
    (tmp_path / "playbooks" / "deploy.yml").write_text("---\n")
    calls = []

    def fake_popen(cmd, **kwargs):
        calls.append(list(cmd))
        return _FakeProc()

    with patch("dotm.sync.subprocess.Popen", side_effect=fake_popen), \
         patch("dotm.sync.get_platform", return_value=list(platform)):
        assert sync_mod.ansible_apply(tmp_path, excluded=excluded, quiet=True)
    assert len(calls) == 1
    return calls[0]


def _extra_vars(cmd) -> dict:
    assert "-e" not in cmd
    assert cmd.count("--extra-vars") == 1
    return json.loads(cmd[cmd.index("--extra-vars") + 1])


def test_ansible_apply_hands_the_play_no_module_list(tmp_path):
    cmd = _run_apply(tmp_path, excluded=["foo", "bar"])
    assert cmd[:2] == ["ansible-playbook", str(tmp_path / "playbooks" / "deploy.yml")]
    assert cmd[cmd.index("-i") + 1] == str(tmp_path / "playbooks" / "inventory")
    assert not any("final_modules" in arg for arg in cmd)
    extra = _extra_vars(cmd)
    assert "final_modules" not in extra


def test_ansible_apply_passes_exclusions_and_platform_as_the_only_extra_vars(tmp_path):
    """The play gets exactly two machine facts from the dotm config: exclusions and platform."""
    cmd = _run_apply(tmp_path, excluded=["foo", "bar"])
    assert _extra_vars(cmd) == {"dotm_excluded_modules": ["foo", "bar"],
                                "dotm_platform": ["macos", "brew", "gui"]}


def test_ansible_apply_passes_empty_exclusions_and_the_macos_default_when_none_configured(tmp_path):
    """A machine with no `platform:` key is a Mac: unchanged behavior for every live machine."""
    cmd = _run_apply(tmp_path, excluded=[])
    assert _extra_vars(cmd) == {"dotm_excluded_modules": [], "dotm_platform": ["macos", "brew", "gui"]}


def test_ansible_apply_passes_the_declared_platform_through(tmp_path):
    cmd = _run_apply(tmp_path, excluded=[], platform=["linux-arm", "apt", "headless"])
    assert _extra_vars(cmd)["dotm_platform"] == ["linux-arm", "apt", "headless"]


def test_ansible_apply_fails_without_deploy_yml(tmp_path):
    with patch("dotm.sync.subprocess.Popen") as popen:
        assert not sync_mod.ansible_apply(tmp_path, excluded=[], quiet=True)
    popen.assert_not_called()


def test_deploy_yml_applies_dotm_exclusions_in_both_resolution_branches():
    text = DEPLOY_YML.read_text()
    # Both candidate-list branches (known, unknown profile) live in deploy.yml, and each one
    # subtracts the exclusions dotm passes before the role filter sees the list.
    branches = re.findall(r"candidate_modules: >-\n(.*?)\n      when:", text, re.S)
    assert len(branches) == 2, "expected one set_fact per branch (known, unknown profile)"
    for body in branches:
        assert "difference(dotm_excluded_modules | default([]))" in body
    # sync.py hands the play no list and no role: deploy.yml is the single resolution point.
    sync_src = Path(sync_mod.__file__).read_text()
    assert "final_modules" not in sync_src
    assert "dotm_role" not in sync_src


def test_deploy_yml_selects_final_modules_from_candidates_by_requires():
    text = DEPLOY_YML.read_text()
    # The role filter loops over the candidate list, reads each module's `requires:` and
    # keeps the module when the machine's capability set covers it.
    select = re.search(r"final_modules: >-\n(.*?)\n      loop: \"\{\{ candidate_modules \}\}\"", text, re.S)
    assert select is not None
    assert ".requires | default([], true)" in select.group(1)
    assert "difference(dotm_capabilities) | length == 0" in select.group(1)
    # The role and the capability set come from the machine's local dotm config, never a
    # host name or an extra var.
    assert "/.config/dotm/config.yml" in text
    assert "dotm_local_config.role" in text
    assert "dotm_local_config.capabilities" in text
    assert "role_capabilities[dotm_role]" in text


def test_deploy_yml_joins_the_declared_platform_into_the_capability_set():
    text = DEPLOY_YML.read_text()
    # The platform dotm passes joins the role's capabilities in the one resolution step, with
    # the macOS default when a machine (or a play run by hand) passes none.
    step = re.search(r"Resolve the machine's capability set\n(.*?)\n\n", text, re.S)
    assert step is not None
    assert "dotm_platform | default(['macos', 'brew', 'gui'])" in step.group(1)
    assert text.count("dotm_platform") == 1
