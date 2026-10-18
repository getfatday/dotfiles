"""op-agent-sign: signature VERIFICATION must work in a plain shell, with no GIT_CONFIG_* env.

Agents get gpg.ssh.allowedSignersFile through GIT_CONFIG_* env (hermes .env, Claude settings), so any
other process (launchd job, cron, a probe, a guard reading %G?) saw no allowed-signers file and every
commit read N. The module therefore ships a user-level git config (XDG ~/.config/git/config) that
points at the module's own allowed_signers. This test stows the module's files into a temp HOME,
signs a commit with a throwaway key (appended to that HOME's allowed_signers) and expects %G? == G
with a scrubbed environment.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[4] / "modules" / "op-agent-sign"
FILES = MODULE / "files"

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None or shutil.which("ssh-keygen") is None, reason="needs git and ssh-keygen"
)


def _env(home: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "XDG_"))}
    env.update(HOME=str(home), GIT_CONFIG_NOSYSTEM="1")
    return env


def _git(home: Path, *args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, env=_env(home), capture_output=True, text=True)


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    shutil.copytree(FILES / ".config", h / ".config")  # what stow links into ~/.config
    return h


def test_module_ships_user_level_allowed_signers_config():
    cfg = FILES / ".config" / "git" / "config"
    assert cfg.is_file(), "modules/op-agent-sign/files/.config/git/config is the verification routing"


def test_plain_shell_resolves_allowed_signers_file(home):
    r = _git(home, "config", "--show-origin", "gpg.ssh.allowedSignersFile")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().endswith("allowed_signers"), r.stdout
    assert str(home / ".config" / "git" / "config") in r.stdout


def test_commit_verifies_G_without_env(home, tmp_path):
    key = tmp_path / "k"
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)], check=True)
    pub = (tmp_path / "k.pub").read_text().split()
    signers = home / ".config" / "op-agent-sign" / "allowed_signers"
    signers.write_text(signers.read_text() + f'test@example.com namespaces="git" {pub[0]} {pub[1]}\n')

    repo = tmp_path / "repo"
    repo.mkdir()
    assert _git(home, "init", "-q", "-b", "main", cwd=repo).returncode == 0
    r = _git(
        home, "-c", "user.name=t", "-c", "user.email=test@example.com", "-c", "gpg.format=ssh",
        "-c", f"user.signingkey={key}", "commit", "-q", "-S", "--allow-empty", "-m", "x", cwd=repo,
    )
    assert r.returncode == 0, r.stderr
    assert _git(home, "log", "-1", "--format=%G?", cwd=repo).stdout.strip() == "G"
