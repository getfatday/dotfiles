"""Tests for dotm.sync: deploy.yml, not dotm, resolves which modules apply."""

import json
import re
from pathlib import Path
from unittest.mock import patch

from dotm import sync as sync_mod

DEPLOY_YML = Path(__file__).resolve().parents[4] / "playbooks" / "deploy.yml"


class _FakeProc:
    pid = 4242
    returncode = 0

    def communicate(self, timeout=None):
        return (b"", b"")


def _run_apply(tmp_path, excluded):
    (tmp_path / "playbooks").mkdir()
    (tmp_path / "playbooks" / "deploy.yml").write_text("---\n")
    calls = []

    def fake_popen(cmd, **kwargs):
        calls.append(list(cmd))
        return _FakeProc()

    with patch("dotm.sync.subprocess.Popen", side_effect=fake_popen):
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


def test_ansible_apply_passes_dotm_exclusions_as_the_only_extra_var(tmp_path):
    cmd = _run_apply(tmp_path, excluded=["foo", "bar"])
    assert _extra_vars(cmd) == {"dotm_excluded_modules": ["foo", "bar"]}


def test_ansible_apply_passes_empty_exclusions_when_none_configured(tmp_path):
    cmd = _run_apply(tmp_path, excluded=[])
    assert _extra_vars(cmd) == {"dotm_excluded_modules": []}


def test_ansible_apply_fails_without_deploy_yml(tmp_path):
    with patch("dotm.sync.subprocess.Popen") as popen:
        assert not sync_mod.ansible_apply(tmp_path, excluded=[], quiet=True)
    popen.assert_not_called()


def test_deploy_yml_applies_dotm_exclusions_in_both_resolution_branches():
    text = DEPLOY_YML.read_text()
    # Every set_fact of final_modules lives in deploy.yml, and each one subtracts the
    # exclusions dotm passes.
    branches = re.findall(r"final_modules: >-\n(.*?)\n      when:", text, re.S)
    assert len(branches) == 2, "expected one set_fact per branch (known, unknown profile)"
    for body in branches:
        assert "difference(dotm_excluded_modules | default([]))" in body
    # sync.py hands the play no list: deploy.yml is the single resolution point.
    sync_src = Path(sync_mod.__file__).read_text()
    assert "final_modules" not in sync_src
