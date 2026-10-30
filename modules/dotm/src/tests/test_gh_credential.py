"""gh wrapper as git credential helper: answer with the login that owns the repo in path=.

git calls `gh auth git-credential get` with host= and path= (credential.useHttpPath). The wrapper
asks gh-account for the owner's login and answers with that login's token; anything it cannot
resolve goes to the real gh with the request unchanged. The real gh is a stub (GH_ACCOUNT_REAL_GH)
that hands out token-for-<user> and records what reached `auth git-credential`; HOME and the
accounts map are temp, so the real map and keyring are never touched.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[4] / "modules" / "git" / "files" / ".local" / "bin"
WRAPPER = BIN / "gh"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")

STUB = """#!/bin/sh
# fake gh: token-for-<user>, records git-credential passthrough, fails everything else (probes)
if [ "$1 $2" = "auth token" ] && [ "$3" = --user ]; then echo "token-for-$4"; exit 0; fi
if [ "$1 $2" = "auth git-credential" ]; then
  cat > "$STUB_LOG.$3"
  [ "$3" = get ] && printf 'username=real-gh\\npassword=real-token\\n'
  exit 0
fi
exit 1
"""

HOSTS = """github.com:
    git_protocol: https
    users:
        ianderson_expedia: {}
        getfatday:
    user: ianderson_expedia
"""

MAP = {"hosts": {"github.com": {
    "default": "ianderson_expedia",
    "owners": {"getfatday": "getfatday", "ExpediaGroup": "ianderson_expedia"},
    "learned": {},
}}}


@pytest.fixture
def env(tmp_path):
    home = tmp_path / "home"
    (home / ".config" / "gh").mkdir(parents=True)
    (home / ".config" / "gh" / "hosts.yml").write_text(HOSTS)
    accounts = tmp_path / "accounts.json"
    accounts.write_text(json.dumps(MAP))
    stub = tmp_path / "real-gh"
    stub.write_text(STUB)
    stub.chmod(0o755)
    e = {k: v for k, v in os.environ.items() if not k.startswith(("GH_", "GITHUB_", "GIT_"))}
    e.update(HOME=str(home), GH_ACCOUNT_REAL_GH=str(stub), GH_ACCOUNT_MAP=str(accounts),
             STUB_LOG=str(tmp_path / "passthrough"), GIT_CONFIG_NOSYSTEM="1",
             GIT_CONFIG_GLOBAL="/dev/null")
    return e


def _cred(env, op, request):
    return subprocess.run([str(WRAPPER), "auth", "git-credential", op], input=request,
                          env=env, capture_output=True, text=True, timeout=120)


def _get(env, path=None):
    req = "protocol=https\nhost=github.com\n" + (f"path={path}\n" if path else "") + "\n"
    return _cred(env, "get", req)


def _passed(env, op):
    p = Path(env["STUB_LOG"] + "." + op)
    return p.read_text() if p.exists() else None


@pytest.mark.parametrize("path,login", [
    ("getfatday/skills.git", "getfatday"),
    ("ExpediaGroup/x.git", "ianderson_expedia"),
    ("someone-else/repo.git", "ianderson_expedia"),  # unknown owner, probes fail -> default
])
def test_get_answers_with_owner_login(env, path, login):
    r = _get(env, path)
    assert r.returncode == 0, r.stderr
    assert r.stdout == f"username={login}\npassword=token-for-{login}\n"
    assert _passed(env, "get") is None


def test_unknown_owner_uses_map_default(env):
    accounts = json.loads(Path(env["GH_ACCOUNT_MAP"]).read_text())
    accounts["hosts"]["github.com"]["default"] = "getfatday"
    Path(env["GH_ACCOUNT_MAP"]).write_text(json.dumps(accounts))
    assert _get(env, "nobody/x.git").stdout.startswith("username=getfatday\n")


def test_no_path_passes_request_to_real_gh(env):
    r = _get(env)
    assert r.stdout == "username=real-gh\npassword=real-token\n"
    assert _passed(env, "get") == "protocol=https\nhost=github.com\n\n"


def test_gh_token_set_passes_through(env):
    r = _get(dict(env, GH_TOKEN="x"), "getfatday/skills.git")
    assert r.stdout.startswith("username=real-gh\n")
    assert "path=getfatday/skills.git" in _passed(env, "get")


def test_token_lookup_failure_passes_through(env):
    Path(env["GH_ACCOUNT_REAL_GH"]).write_text(STUB.replace('echo "token-for-$4"; exit 0', "exit 1"))
    r = _get(env, "getfatday/skills.git")
    assert r.stdout.startswith("username=real-gh\n")


@pytest.mark.parametrize("op", ["store", "erase"])
def test_store_erase_refeed_unchanged(env, op):
    req = "protocol=https\nhost=github.com\npath=getfatday/skills.git\nusername=getfatday\npassword=p\n\n"
    r = _cred(env, op, req)
    assert r.returncode == 0 and r.stdout == ""
    assert _passed(env, op) == req


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_git_credential_fill_routes_through_wrapper(env):
    helper = f"!{WRAPPER} auth git-credential"
    r = subprocess.run(
        ["git", "-c", "credential.https://github.com.helper=",
         "-c", f"credential.https://github.com.helper={helper}",
         "-c", "credential.https://github.com.useHttpPath=true", "credential", "fill"],
        input="protocol=https\nhost=github.com\npath=getfatday/skills.git\n\n",
        env=dict(env, GIT_TERMINAL_PROMPT="0"), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert "username=getfatday\n" in r.stdout and "password=token-for-getfatday\n" in r.stdout
