"""F-TDD-1 in the dotfiles CI: a code change carries a test or a recorded `tdd-exempt:` line."""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest
import yaml

CI = Path(__file__).resolve().parents[1]
ROOT = CI.parent
FIXTURES = CI / "tests" / "fixtures" / "tdd"
GUARD = CI / "tdd_guard.py"

spec = importlib.util.spec_from_file_location("tdd_guard", GUARD)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

vspec = importlib.util.spec_from_file_location("verify", CI / "verify.py")
verify = importlib.util.module_from_spec(vspec)
vspec.loader.exec_module(verify)


def run_guard(*args, env=None):
    base = {k: v for k, v in os.environ.items() if not k.startswith("TDD_")}
    base.update(env or {})
    return subprocess.run([sys.executable, "-B", str(GUARD), *args], capture_output=True, text=True, env=base)


# ---- the Assertion fixtures: the exit code is the verdict
@pytest.mark.parametrize("name,code", [
    ("code-no-test", 1),
    ("workflow-no-test", 1),
    ("code-with-test", 0),
    ("editorial-only", 0),
])
def test_fixture_exit_codes(name, code):
    r = run_guard("--diff", str(FIXTURES / f"{name}.diff"))
    assert r.returncode == code, r.stdout + r.stderr


def test_red_message_names_the_file_the_rule_and_the_way_out():
    r = run_guard("--diff", str(FIXTURES / "code-no-test.diff"))
    assert r.returncode == 1
    assert "FINDING F-TDD-1: code change without a test" in r.stdout
    assert "modules/example/setup.sh" in r.stdout
    assert "tdd-exempt: <reason>" in r.stdout
    assert ".ci/tests/**" in r.stdout


# ---- classification with the dotfiles globs
@pytest.mark.parametrize("path,kind", [
    ("modules/hermes/setup.sh", "code"),
    ("modules/hermes/check.sh", "code"),
    ("modules/dotm/src/dotm/cli.py", "code"),
    ("modules/dotm/src/dotm/data.yml", "code"),
    (".ci/verify.py", "code"),
    (".ci/tdd_guard.py", "code"),
    (".github/workflows/verify.yml", "code"),
    ("modules/dotm/src/tests/test_role.py", "test"),
    (".ci/tests/test_gate.py", "test"),
    (".ci/tests/fixtures/tdd/code-no-test.diff", "test"),
    ("modules/op-agent-sign/tests/run.sh", "test"),
    ("docs/design/x.md", "editorial"),
    ("README.md", "editorial"),
    ("modules/git/files/.gitconfig", "other"),
    (".ci/README.md", "other"),
    ("playbooks/profiles.yml", "other"),
])
def test_classification(path, kind):
    assert guard.load_globs().classify(path) == kind


def test_deleting_code_needs_no_test():
    result = guard.evaluate([("D", "modules/old/setup.sh")], guard.load_globs())
    assert result["verdict"] == "green"


def test_code_plus_test_is_green_and_code_alone_is_red():
    g = guard.load_globs()
    assert guard.evaluate([("M", "modules/a/setup.sh"), ("A", "modules/a/tests/run.sh")], g)["verdict"] == "green"
    assert guard.evaluate([("M", "modules/a/setup.sh")], g)["verdict"] == "red"


# ---- exemptions: the record, never silence
def test_pr_body_exemption_passes_and_is_reported():
    body = "Fix a typo in a comment.\n\ntdd-exempt: comment-only change\n"
    r = run_guard("--diff", str(FIXTURES / "code-no-test.diff"), env={"TDD_PR_BODY": body})
    assert r.returncode == 0, r.stdout
    assert "FINDING F-TDD-1: tdd-exempt: comment-only change" in r.stdout


@pytest.mark.parametrize("body", ["", "no exemption here", "tdd-exempt: <reason>", "tdd-exempt: ", "see tdd-exempt: not at line start"])
def test_missing_or_placeholder_exemption_stays_red(body):
    r = run_guard("--diff", str(FIXTURES / "code-no-test.diff"), env={"TDD_PR_BODY": body})
    assert r.returncode == 1, r.stdout


def test_pr_body_cannot_exempt_a_change_that_has_a_test():
    r = run_guard("--diff", str(FIXTURES / "code-with-test.diff"), env={"TDD_PR_BODY": "tdd-exempt: x y z"})
    assert r.returncode == 0
    assert "FINDING" not in r.stdout


def test_usage_and_io_errors_exit_2(tmp_path):
    assert run_guard("--diff", str(tmp_path / "missing.diff")).returncode == 2
    assert run_guard("--base", "no-such-ref", "--repo", str(tmp_path)).returncode == 2


# ---- git mode: what CI runs (--base origin/main --head HEAD, diff from the merge base)
def git(repo, *args):
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, env=env)


def commit(repo, files, message):
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-b", "main")
    commit(tmp_path, {"modules/a/setup.sh": "echo 1\n", "README.md": "# r\n"}, "base")
    git(tmp_path, "checkout", "-b", "feature")
    return tmp_path


def test_git_range_red_then_green_with_a_test(repo):
    commit(repo, {"modules/a/setup.sh": "echo 2\n"}, "change a script")
    assert run_guard("--repo", str(repo), "--base", "main", "--head", "HEAD").returncode == 1
    commit(repo, {"modules/a/tests/run.sh": "true\n"}, "add its test")
    r = run_guard("--repo", str(repo), "--base", "main", "--head", "HEAD")
    assert r.returncode == 0, r.stdout


def test_git_range_commit_message_exemption(repo):
    commit(repo, {"modules/a/setup.sh": "echo 2\n"}, "change a script\n\ntdd-exempt: output-only change, no behaviour\n")
    r = run_guard("--repo", str(repo), "--base", "main", "--head", "HEAD")
    assert r.returncode == 0
    assert "tdd-exempt: output-only change, no behaviour" in r.stdout


def test_git_range_ignores_what_main_gained_after_the_branch_point(repo):
    commit(repo, {"README.md": "# changed\n"}, "docs on the branch")
    git(repo, "checkout", "main")
    commit(repo, {"modules/a/setup.sh": "echo main-moved\n"}, "main moves on")
    git(repo, "checkout", "feature")
    assert run_guard("--repo", str(repo), "--base", "main", "--head", "HEAD").returncode == 0


def test_git_range_with_no_change_is_green(repo):
    assert run_guard("--repo", str(repo), "--base", "main", "--head", "HEAD").returncode == 0


# ---- wiring: the guard is a required part of the aggregate gate
def test_vendored_header_records_the_lab_commit():
    head = GUARD.read_text().splitlines()[:3]
    assert head[0].startswith("#!")
    assert re.search(r"lab commit [0-9a-f]{7,40}", head[1]), head[1]


def test_contract_requires_the_tdd_profile_and_runs_the_guard_on_the_pr_diff():
    spec = verify.contract()
    assert "tdd" in spec["required_profiles"]
    assert spec["profiles"]["tdd"]["checks"] == [["{python}", ".ci/tdd_guard.py", "--base", "origin/main", "--head", "HEAD"]]
    assert set(spec["required_profiles"]) == set(spec["profiles"])


def test_workflow_has_a_tdd_job_and_the_aggregate_needs_it():
    wf = yaml.safe_load((ROOT / ".github/workflows/verify.yml").read_text())
    job = wf["jobs"]["tdd"]
    steps = job["steps"]
    checkout = next(s for s in steps if str(s.get("uses", "")).startswith("actions/checkout"))
    assert checkout["with"]["fetch-depth"] == 0  # origin/main...HEAD needs the history
    run = next(s for s in steps if "verify.py run tdd" in s.get("run", ""))
    assert "github.event.pull_request.body" in run["env"]["TDD_PR_BODY"]
    acceptance = wf["jobs"]["acceptance"]
    assert acceptance["name"] == "dotm-acceptance"
    assert "tdd" in acceptance["needs"]
    needs_env = next(s for s in acceptance["steps"] if s.get("name") == "Require all jobs and current receipts")["env"]["VERIFICATION_NEEDS"]
    assert "needs.tdd.result" in needs_env
    # every required profile has a job and a needs entry, so a skipped job cannot slip through
    assert set(verify.contract()["required_profiles"]) == set(acceptance["needs"])


def test_aggregate_rejects_a_run_without_tdd_evidence():
    spec = verify.contract()
    ident = {"commit": "a" * 40, "input_sha256": "b" * 64, "contract_sha256": "c" * 64}
    receipts = [{"profile": p, "identity": ident, "status": "passed", "inputs_unchanged": True, "finished_at": 100,
                 "checks": [{"command": c, "exit_code": 0} for c in spec["profiles"][p]["checks"]]}
                for p in spec["required_profiles"]]
    needs = {p: "success" for p in spec["required_profiles"]}
    assert verify.validate_receipts(spec, ident, receipts, needs, now=100)
    with pytest.raises(ValueError):
        verify.validate_receipts(spec, ident, [r for r in receipts if r["profile"] != "tdd"], needs, now=100)
    with pytest.raises(ValueError):
        verify.validate_receipts(spec, ident, receipts, {**needs, "tdd": "failure"}, now=100)
    with pytest.raises(ValueError):
        verify.validate_receipts(spec, ident, receipts, {k: v for k, v in needs.items() if k != "tdd"}, now=100)
