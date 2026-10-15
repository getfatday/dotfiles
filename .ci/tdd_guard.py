#!/usr/bin/env python3
# vendored from hyp-hermes tools/guards/tdd_guard.py @ lab commit 04c56cdf (branch hyp-hermes/t_a44a8ba2-tdd-guard); local changes: dotfiles globs embedded (DEFAULT_CFG), repo root is the parent of .ci, TDD_PR_BODY env
"""tdd_guard.py - F-TDD-1: a code change without a test is a finding; the exemption is the record, never silence.

  python3 .ci/tdd_guard.py --diff FILE|-            # unified diff or `git diff --name-status` output
  python3 .ci/tdd_guard.py --repo R --base main --head BRANCH     # git diff --name-status base...head (+ the commit messages)
  python3 .ci/tdd_guard.py --repo R --staged                      # what the pre-commit hook gates
  python3 .ci/tdd_guard.py --repo R --rev REV                     # the change one commit introduced
  options: --globs FILE (JSON; default: the dotfiles globs embedded below in DEFAULT_CFG)  --json
           --message TEXT / --message-file FILE / --pr-body-file FILE / --exempt REASON   (exemption sources; env TDD_EXEMPT and TDD_PR_BODY too)
           --record [--ledger-dir DIR] [--ref NAME] [--source NAME]   append used exemptions to <ledger>/tdd-exemptions.jsonl

Every changed path is classified (DEFAULT_CFG below; precedence test > editorial > code > other; deletions are ignored). The set is
  code       a code path changed (modules/*/setup.sh, modules/dotm/src/**, .ci/*.py, workflows, ...), no editorial path
  editorial  only docs / research / ledger / journal-fragment / *.md paths changed
  mixed      code and editorial together
  none       only test or unclassified paths
RED (exit 1) when a code path changes and no test path changes in the same set, unless the change carries `tdd-exempt: <reason>` (a
line starting with it in a commit message / PR body, `--exempt`, or card metadata passed as TDD_EXEMPT). An exemption that is USED
(the change would be red) exits 0, prints `FINDING F-TDD-1: tdd-exempt: ...` and, with --record, is appended to
ledger/tdd-exemptions.jsonl (deduped on ref + source + reason) so exemptions are visible, counted and trend-able.
Exit: 0 green / exempt, 1 red, 2 usage or IO error. Stdlib only, Python 3.9.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
# Dotfiles classification. Precedence per path: test, then editorial (minus editorial_exclude), then code, else other.
DEFAULT_CFG = {
    "code": ["modules/*/setup.sh", "modules/*/check.sh", "modules/dotm/src/**", ".ci/*.py", ".github/workflows/**"],
    "editorial": ["docs/**", "*.md"],
    "editorial_exclude": ["modules/dotm/src/**", ".ci/**", ".github/**"],
    "test": ["modules/dotm/src/tests/**", ".ci/tests/**", "modules/*/tests/**"],
}
LEDGER_NAME = "tdd-exemptions.jsonl"
RULE = "a code change without a test is a finding; the exemption is the record, never silence"
FID = "F-TDD-1"

EXEMPT_RX = re.compile(r"(?im)^[ \t>*-]*tdd-exempt:[ \t]*(\S.*?)[ \t]*$")
PLACEHOLDER_REASONS = {"<reason>", "reason", "..."}


# ---------------------------------------------------------------- globs
def _glob_rx(pat):
    """Glob -> compiled regex. `**` crosses `/`, `*`/`?` do not; no `/` in the pattern = match the file name at any depth."""
    anywhere = "/" not in pat
    out, i = [], 0
    if pat.startswith("**/"):
        out.append("(?:.*/)?")
        i = 3
    while i < len(pat):
        c = pat[i]
        if pat.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pat.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    body = "".join(out)
    return re.compile(("(?:.*/)?" if anywhere else "") + body + r"\Z", re.S)


class Globs:
    def __init__(self, cfg):
        self.rx = {k: [_glob_rx(p) for p in cfg.get(k, [])] for k in ("code", "editorial", "editorial_exclude", "test")}

    def _any(self, key, path):
        return any(r.match(path) for r in self.rx[key])

    def classify(self, path):
        """-> test | editorial | code | other"""
        if self._any("test", path):
            return "test"
        if self._any("editorial", path) and not self._any("editorial_exclude", path):
            return "editorial"
        if self._any("code", path):
            return "code"
        return "other"


def load_globs(path=None):
    if not path:
        return Globs(DEFAULT_CFG)
    with open(path, encoding="utf-8") as f:
        return Globs(json.load(f))


# ---------------------------------------------------------------- change sets
def parse_name_status(text):
    """`git diff --name-status` text -> [(status_letter, path)]. Renames/copies report the new path."""
    out = []
    for line in text.splitlines():
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2 and re.match(r"^[A-Z]\d*$", parts[0]):
            out.append((parts[0][0], parts[-1]))
    return out


_HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")


def _strip_prefix(p, prefix):
    p = p.split("\t")[0].strip()
    return p[len(prefix):] if p.startswith(prefix) else p


def parse_unified(text):
    """Unified diff text -> (entries [(status, path)], preamble). Hunk line counts keep content lines that look like headers out."""
    entries, cur, pre = [], None, []
    seen_file = False
    old_left = new_left = 0
    pending_old = None
    for line in text.splitlines():
        if old_left > 0 or new_left > 0:
            if line.startswith("\\"):
                continue
            if line.startswith("+"):
                new_left -= 1
            elif line.startswith("-"):
                old_left -= 1
            else:
                old_left -= 1
                new_left -= 1
            continue
        m = _HUNK.match(line)
        if m:
            old_left = int(m.group(1)) if m.group(1) is not None else 1
            new_left = int(m.group(2)) if m.group(2) is not None else 1
            continue
        if line.startswith("diff --git "):
            seen_file = True
            mm = re.match(r"^diff --git a/(.*) b/(.*)$", line)
            cur = {"status": "M", "path": mm.group(2) if mm else line.split(" b/")[-1]}
            entries.append(cur)
            pending_old = None
            continue
        if line.startswith("--- "):
            seen_file = True
            pending_old = _strip_prefix(line[4:], "a/")
            if cur is not None and cur.get("_done"):
                cur = None  # plain `diff -u`: a new file section
            continue
        if line.startswith("+++ "):
            new = line[4:].split("\t")[0].strip()
            if cur is None:
                cur = {"status": "M", "path": None}
                entries.append(cur)
            if new == "/dev/null":
                cur["status"] = "D"
                if pending_old and pending_old != "/dev/null":
                    cur["path"] = pending_old
            else:
                cur["path"] = _strip_prefix(new, "b/")
                if pending_old == "/dev/null":
                    cur["status"] = "A"
            cur["_done"] = True
            pending_old = None
            continue
        if cur is not None:
            if line.startswith("new file mode"):
                cur["status"] = "A"
            elif line.startswith("deleted file mode"):
                cur["status"] = "D"
            elif line.startswith("rename to "):
                cur["status"] = "R"
                cur["path"] = line[len("rename to "):]
        elif not seen_file:
            pre.append(line)
    return [(e["status"], e["path"]) for e in entries if e.get("path")], "\n".join(pre)


def parse_change_text(text):
    """Auto-detect name-status vs unified diff. -> (entries, preamble)."""
    for line in text.splitlines():
        if line.strip():
            if re.match(r"^[A-Z]\d*\t", line):
                return parse_name_status(text), ""
            break
    return parse_unified(text)


def _git(repo, *args):
    r = subprocess.run(["git", "-C", repo, "-c", "core.quotepath=off"] + list(args), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args[:3]), r.stderr.decode("utf-8", "replace").strip()[:200]))
    return r.stdout.decode("utf-8", "replace")


def changes_from_git(repo, base=None, head="HEAD", staged=False, rev=None):
    """-> (entries, messages [str], ref). `base...head` uses the merge base, like a PR diff."""
    if staged:
        ref = "staged"
        try:
            ref = "staged:" + _git(repo, "write-tree").strip()[:12]
        except RuntimeError:
            pass
        return parse_name_status(_git(repo, "diff", "--cached", "--name-status", "-M")), [], ref
    if rev:
        sha = _git(repo, "rev-parse", "--verify", rev + "^{commit}").strip()
        parents = _git(repo, "rev-list", "--parents", "-n", "1", sha).split()[1:]
        parent = parents[0] if parents else "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
        names = _git(repo, "diff", "--name-status", "-M", parent, sha)
        return parse_name_status(names), [_git(repo, "log", "-1", "--format=%B", sha)], sha
    sha = _git(repo, "rev-parse", "--verify", head + "^{commit}").strip()
    names = _git(repo, "diff", "--name-status", "-M", "%s...%s" % (base, head))
    msgs = [m for m in _git(repo, "log", "--format=%B%x00", "%s..%s" % (base, head)).split("\0") if m.strip()]
    return parse_name_status(names), msgs, sha


# ---------------------------------------------------------------- verdict
def find_exemptions(sources):
    """sources: [(label, text)] -> [{source, reason}] (deduped, placeholder reasons ignored)."""
    out, seen = [], set()
    for label, text in sources:
        for m in EXEMPT_RX.finditer(text or ""):
            reason = " ".join(m.group(1).split())
            if len(reason) < 3 or reason.lower() in PLACEHOLDER_REASONS or (label, reason) in seen:
                continue
            seen.add((label, reason))
            out.append({"source": label, "reason": reason})
    return out


def evaluate(entries, globs, exemption_sources=()):
    cls = {"code": [], "editorial": [], "test": [], "other": []}
    for st, path in entries:
        if st == "D":  # deleting a file is not a change that needs a new test
            continue
        bucket = cls[globs.classify(path)]
        if path not in bucket:
            bucket.append(path)
    if cls["code"] and cls["editorial"]:
        kind = "mixed"
    elif cls["code"]:
        kind = "code"
    elif cls["editorial"]:
        kind = "editorial"
    else:
        kind = "none"
    red = bool(cls["code"]) and not cls["test"]
    exemptions = find_exemptions(exemption_sources) if red else []
    verdict = "green" if not red else ("exempt" if exemptions else "red")
    findings = []
    if verdict == "red":
        findings.append("%s: code change without a test: %d code file(s), no test file in the same change" % (FID, len(cls["code"])))
    elif verdict == "exempt":
        findings.append("%s: tdd-exempt: %s (%d code file(s) without a test)" % (FID, "; ".join(e["reason"] for e in exemptions), len(cls["code"])))
    return {"verdict": verdict, "kind": kind, "exit": 1 if verdict == "red" else 0, "code": cls["code"], "editorial": cls["editorial"],
            "test": cls["test"], "other": cls["other"], "exemptions": exemptions, "findings": findings, "rule": RULE}


def check_staged(repo, globs=None, env=None):
    """pre-commit entry: (result, ref). Exemption from TDD_EXEMPT (the commit message does not exist yet at pre-commit)."""
    env = os.environ if env is None else env
    entries, _msgs, ref = changes_from_git(repo, staged=True)
    return evaluate(entries, globs or load_globs(), _env_sources(env)), ref


def _env_sources(env):
    v = env.get("TDD_EXEMPT", "").strip()
    out = [("env", "tdd-exempt: " + v)] if v else []
    body = env.get("TDD_PR_BODY", "")  # CI passes the pull request body here; its `tdd-exempt:` line is the exemption
    return out + ([("pr-body", body)] if body.strip() else [])


# ---------------------------------------------------------------- record
def record_exemptions(result, ledger_dir, ref, source, now=None):
    """Append used exemptions to <ledger_dir>/tdd-exemptions.jsonl; skip a row already there (ref, source, reason). -> rows written."""
    if result["verdict"] != "exempt":
        return []
    path = os.path.join(ledger_dir, LEDGER_NAME)
    have = set()
    if os.path.isfile(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                have.add((r.get("ref"), r.get("source"), r.get("reason")))
    ts = dt.datetime.fromtimestamp(now, dt.timezone.utc) if now is not None else dt.datetime.now(dt.timezone.utc)
    rows = []
    for e in result["exemptions"]:
        key = (ref, source, e["reason"])
        if key in have:
            continue
        have.add(key)
        rows.append({"id": FID, "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"), "ref": ref, "source": source, "via": e["source"],
                     "reason": e["reason"], "n_code_files": len(result["code"]), "code_files": result["code"][:20]})
    if rows:
        os.makedirs(ledger_dir, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows


# ---------------------------------------------------------------- output
def render(result, limit=10):
    lines = ["tdd-guard: %s  kind=%s code=%d test=%d editorial=%d other=%d" % (
        result["verdict"].upper(), result["kind"], len(result["code"]), len(result["test"]), len(result["editorial"]), len(result["other"]))]
    if result["verdict"] != "green":
        for p in result["code"][:limit]:
            lines.append("  code without a test: " + p)
        if len(result["code"]) > limit:
            lines.append("  ... (%d more)" % (len(result["code"]) - limit))
    for f in result["findings"]:
        lines.append("FINDING " + f)
    if result["verdict"] == "red":
        lines.append("  fix: add or change a test in the same change (modules/dotm/src/tests/**, .ci/tests/**, modules/*/tests/**), or carry a line")
        lines.append("  `tdd-exempt: <reason>` (commit trailer, PR body, card metadata). Rule: " + RULE)
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--diff", metavar="FILE", help="unified diff or name-status output ('-' = stdin)")
    ap.add_argument("--repo", help="git repo for --base/--head, --staged, --rev (default: this repo)")
    ap.add_argument("--base")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--rev")
    ap.add_argument("--globs", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--message", action="append", default=[], help="commit message text carrying a possible `tdd-exempt:` trailer")
    ap.add_argument("--message-file", action="append", default=[])
    ap.add_argument("--pr-body-file", action="append", default=[])
    ap.add_argument("--exempt", action="append", default=[], metavar="REASON", help="card-metadata exemption reason")
    ap.add_argument("--record", action="store_true", help="append a used exemption to the ledger")
    ap.add_argument("--ledger-dir")
    ap.add_argument("--ref")
    ap.add_argument("--source", default="cli")
    a = ap.parse_args(argv)
    modes = [bool(a.diff), bool(a.base), a.staged, bool(a.rev)]
    if sum(modes) != 1:
        ap.error("give exactly one of --diff, --base (with --head), --staged, --rev")
    try:
        globs = load_globs(a.globs)
        sources = [("message", m) for m in a.message]
        for label, files in (("message", a.message_file), ("pr-body", a.pr_body_file)):
            for p in files:
                with open(p, encoding="utf-8", errors="replace") as f:
                    sources.append((label, f.read()))
        sources += [("metadata", "tdd-exempt: " + r) for r in a.exempt] + _env_sources(os.environ)
        repo = os.path.abspath(a.repo or ROOT)
        if a.diff:
            text = sys.stdin.read() if a.diff == "-" else open(a.diff, encoding="utf-8", errors="replace").read()
            entries, pre = parse_change_text(text)
            sources.append(("diff-header", pre))
            ref = a.ref or "diff:" + hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:12]
        else:
            entries, msgs, gref = changes_from_git(repo, a.base, a.head, a.staged, a.rev)
            sources += [("commit", m) for m in msgs]
            ref = a.ref or gref
    except (OSError, RuntimeError) as e:
        print("tdd-guard: %s" % e, file=sys.stderr)
        return 2
    result = evaluate(entries, globs, sources)
    if a.record:
        record_exemptions(result, a.ledger_dir or os.path.join(repo, "ledger"), ref, a.source)
    if a.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(render(result))
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main())
