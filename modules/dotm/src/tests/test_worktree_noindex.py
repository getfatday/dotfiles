"""worktree-noindex: every worktree parent dir and scratch root gets an empty .metadata_never_index.

Runs modules/worktree-noindex/noindex.sh (and check.sh) against a fixture ~/src, never the real one.
Spotlight's mds_stores re-indexed every card worktree and every merge-gate scratch clone (110-135% CPU
for 2 d 15 h); the marker file keeps it out. The script must be declarative and idempotent, create
nothing but the marker, delete nothing, and never touch directories that do not exist.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[4] / "modules" / "worktree-noindex"
NOINDEX = MODULE / "noindex.sh"
CHECK = MODULE / "check.sh"
MARK = ".metadata_never_index"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")


@pytest.fixture
def fx(tmp_path):
    home = tmp_path / "home"
    src = home / "src"
    for rel in (
        "a/.worktrees/t_1",
        "b__worktrees/topic",
        "c/.claude/worktrees/x",
        "d/.git",  # a repo with no worktree dir: must stay untouched
        ".hermes/profiles/p1/cache/scratch/merge-done.abc",
    ):
        (home / "src" / rel if not rel.startswith(".hermes") else home / rel).mkdir(parents=True)
    tmp = tmp_path / "T"
    tmp.mkdir()
    return {"home": home, "src": src, "tmp": tmp}


def run(script, fx, *args):
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(fx["home"]),
        "NOINDEX_SRC_ROOT": str(fx["src"]),
        "NOINDEX_TMP_ROOTS": str(fx["tmp"]),
    }
    return subprocess.run(["bash", str(script), *args], env=env, capture_output=True, text=True)


def marked(fx):
    return sorted(str(p.relative_to(fx["home"].parent)) for p in fx["home"].parent.rglob(MARK))


def test_marks_every_worktree_parent_and_scratch_root(fx):
    r = run(NOINDEX, fx)
    assert r.returncode == 0, r.stderr
    root = fx["home"].parent
    assert marked(fx) == sorted(
        [
            "home/src/a/.worktrees/" + MARK,
            "home/src/b__worktrees/" + MARK,
            "home/src/c/.claude/worktrees/" + MARK,
            "home/.hermes/profiles/p1/cache/scratch/" + MARK,
            "T/" + MARK,
        ]
    )
    assert "dirs=5 created=5 missing=0" in r.stdout
    for p in root.rglob(MARK):
        assert p.stat().st_size == 0, "the marker is an empty file"


def test_second_run_changes_nothing(fx):
    run(NOINDEX, fx)
    before = marked(fx)
    r = run(NOINDEX, fx)
    assert r.returncode == 0
    assert "created=0" in r.stdout and "created " not in r.stdout.replace("created=0", "")
    assert marked(fx) == before


def test_does_not_create_directories_or_mark_plain_repos(fx):
    run(NOINDEX, fx)
    assert not (fx["src"] / "d" / ".worktrees").exists()
    assert not (fx["src"] / "d" / MARK).exists()
    assert not (fx["src"] / "d" / ".git" / MARK).exists()
    # the worktree contents themselves are not marked
    assert not (fx["src"] / "a" / ".worktrees" / "t_1" / MARK).exists()


def test_existing_marker_and_files_are_left_alone(fx):
    marker = fx["src"] / "a" / ".worktrees" / MARK
    marker.write_text("keep\n")
    keep = fx["src"] / "a" / ".worktrees" / "t_1" / "file.txt"
    keep.write_text("data")
    assert run(NOINDEX, fx).returncode == 0
    assert marker.read_text() == "keep\n"
    assert keep.read_text() == "data"


def test_check_reports_missing_and_creates_nothing(fx):
    r = run(CHECK, fx)
    assert r.returncode == 1
    assert marked(fx) == []
    assert f"MISSING {fx['src'].resolve()}/a/.worktrees/{MARK}" in r.stdout
    assert "missing=5" in r.stdout


def test_check_passes_after_apply(fx):
    run(NOINDEX, fx)
    r = run(CHECK, fx)
    assert r.returncode == 0, r.stdout
    assert "missing=0" in r.stdout


def test_a_new_worktree_dir_is_marked_on_the_next_run(fx):
    run(NOINDEX, fx)
    (fx["src"] / "e" / ".worktrees").mkdir(parents=True)
    assert run(CHECK, fx).returncode == 1
    assert run(NOINDEX, fx).returncode == 0
    assert (fx["src"] / "e" / ".worktrees" / MARK).is_file()


def test_missing_roots_are_not_an_error(tmp_path):
    fx = {"home": tmp_path / "h", "src": tmp_path / "h" / "no-src", "tmp": tmp_path / "no-tmp"}
    fx["home"].mkdir()
    r = run(NOINDEX, fx)
    assert r.returncode == 0, r.stderr
    assert "dirs=0" in r.stdout


def test_module_is_wired_into_the_playbooks():
    root = MODULE.parents[1]
    assert "- worktree-noindex" in (root / "playbooks" / "profiles.yml").read_text()
    deploy = (root / "playbooks" / "deploy.yml").read_text()
    assert "worktree-noindex/noindex.sh" in deploy and "'worktree-noindex' in final_modules" in deploy
