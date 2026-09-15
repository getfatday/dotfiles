"""Adversarial tests for the watchdog PreToolUse hook guard.

Runs modules/dotm/files/.local/libexec/dotm-watchdog/hook-guard.py as a subprocess, the way
Claude Code invokes it: payload JSON on stdin, `--log`, `--state-dir` and `--repo` as argv.
Contract: exit 0 allows the call, exit 2 denies it (reason on stderr), and every call is
appended to the log as one JSON line with `denied` set.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = (
    Path(__file__).resolve().parents[2]
    / "files" / ".local" / "libexec" / "dotm-watchdog" / "hook-guard.py"
)
REPO = "getfatday/dotfiles"


@pytest.fixture
def env(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "report.md").write_text("report\n")
    outside = tmp_path / "outside.md"
    outside.write_text("secret\n")
    return {"state": state, "log": tmp_path / "hook.log", "outside": outside}


def run_guard(env, payload):
    proc = subprocess.run(
        [sys.executable, str(GUARD), "--log", str(env["log"]),
         "--state-dir", str(env["state"]), "--repo", REPO],
        input=json.dumps(payload), text=True, capture_output=True,
    )
    return proc


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def last_record(env):
    return json.loads(env["log"].read_text().splitlines()[-1])


def hostile_cases(env):
    body = env["state"] / "body.md"
    return [
        ("gh issue view", bash(f"gh issue view 12 --repo {REPO}")),
        ("inline --body", bash(f"gh issue create --repo {REPO} --title t --body 'inline text'")),
        ("other repo", bash("gh issue list --repo someone-else/dotfiles")),
        ("pipe", bash(f"gh issue list --repo {REPO} | cat")),
        ("semicolon", bash(f"gh issue list --repo {REPO}; rm -rf ~")),
        ("backtick", bash(f"gh issue list --repo {REPO} --label `whoami`")),
        ("subshell", bash(f"gh issue list --repo {REPO} --label $(whoami)")),
        ("body-file outside state dir", bash(f"gh issue create --repo {REPO} --title t --body-file {env['outside']}")),
        ("body-file stdin", bash(f"gh issue comment 12 --repo {REPO} --body-file -")),
        ("attached shorthand", bash(f"gh issue comment 12 --repo {REPO} -F{body}")),
        ("missing repo", bash("gh issue list --state open")),
        ("Read outside state dir", {"tool_name": "Read", "tool_input": {"file_path": str(env["outside"])}}),
        ("Grep", {"tool_name": "Grep", "tool_input": {"pattern": "x", "path": str(env["state"])}}),
        ("Edit", {"tool_name": "Edit", "tool_input": {"file_path": str(env["state"] / "report.md"),
                                                       "old_string": "a", "new_string": "b"}}),
        ("Write", {"tool_name": "Write", "tool_input": {"file_path": str(env["state"] / "x"), "content": ""}}),
        ("empty command", bash("")),
        ("malformed payload", {"tool_name": "Bash", "tool_input": "gh issue list"}),
    ]


def test_hostile_payloads_are_denied(env):
    for label, payload in hostile_cases(env):
        proc = run_guard(env, payload)
        assert proc.returncode == 2, f"{label}: expected deny, got exit {proc.returncode}"
        assert "denied" in proc.stderr, f"{label}: no denial reason on stderr"
        rec = last_record(env)
        assert rec["denied"] is True and rec["reason"], f"{label}: log record not marked denied"


def test_legitimate_commands_are_allowed(env):
    body = env["state"] / "body.md"
    body.write_text("hello\n")
    allowed = [
        bash(f"gh issue list --repo {REPO} --label watchdog --state open --json number,title --limit 20"),
        bash(f"gh issue create --repo {REPO} --title 'sync failed' --label watchdog --body-file {body}"),
        bash(f"gh issue comment 42 --repo {REPO} --body-file {body}"),
        bash(f"gh issue comment 42 -R {REPO} -F {body}"),
        {"tool_name": "Read", "tool_input": {"file_path": str(env["state"] / "report.md")}},
    ]
    for payload in allowed:
        proc = run_guard(env, payload)
        assert proc.returncode == 0, f"{payload}: expected allow, got {proc.returncode}: {proc.stderr}"
        assert last_record(env)["denied"] is False


def test_symlink_escape_from_state_dir_is_denied(env):
    link = env["state"] / "link.md"
    link.symlink_to(env["outside"])
    proc = run_guard(env, {"tool_name": "Read", "tool_input": {"file_path": str(link)}})
    assert proc.returncode == 2
    proc = run_guard(env, bash(f"gh issue comment 1 --repo {REPO} --body-file {link}"))
    assert proc.returncode == 2


def test_unparseable_stdin_is_denied(env):
    proc = subprocess.run(
        [sys.executable, str(GUARD), "--log", str(env["log"]), "--state-dir", str(env["state"]), "--repo", REPO],
        input="{not json", text=True, capture_output=True,
    )
    assert proc.returncode == 2
