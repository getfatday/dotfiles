#!/usr/bin/env python3
"""hook-guard.py: PreToolUse hook for the H-012 watchdog session. Logger and enforcing guard.

Stdlib only (json, re, shlex, sys, os, time). Reads the hook payload on stdin, appends one JSON
line per tool call to the log, and exits 2 (deny; stderr goes back to the model) when the call
falls outside the reporter's lane. Every denial is logged with denied:true and a reason, so the
hook log is a complete record of what the session attempted.

Usage (as written into the session's --settings file by watchdog.py):
    python3 hook-guard.py --log <hook.log path> --state-dir <state dir> --repo <owner/repo>

Rules:
  Bash   command tokens must start with `gh issue list|create|comment`;
         raw command must not contain $ ` ; | & > < or a newline;
         every `-` token must be an exact spelling from the per-subcommand flag allowlist below
         (or `--long=value` for an allowlisted long flag); attached shorthand (`-Fpath`, `-F=path`,
         `-Rowner/repo`) and any flag not on the list are denied;
         every --repo/-R value must equal the allowed repo, and one is required;
         --body-file/-F must point inside the state dir (never `-`);
         values must not start with `-`; positionals: none for list and create, one issue number for comment.
  Read   file_path must resolve inside the state dir.
  other  denied.
Flag allowlist (gh 2.88 spellings):
  list     --repo -R  --label -l  --state -s  --json  --limit -L
  create   --repo -R  --label -l  --title -t  --body-file -F
  comment  --repo -R  --body-file -F
Denied by omission: --body/-b (inline text is unscanned), --edit-last, --create-if-none, --search/-S,
--jq/-q, --template/-t on list, --web/-w, --editor/-e, --app, --author, --assignee, --milestone, --project.
The permission layer (--permission-mode dontAsk with the allowedTools list) accepts any gh issue
argument; this hook is the argument-level gate and the log.
"""
import json
import os
import re
import shlex
import sys
import time


def main() -> int:
    args = sys.argv[1:]
    opts = {"--log": None, "--state-dir": None, "--repo": "getfatday/dotfiles"}
    i = 0
    while i < len(args):
        if args[i] in opts and i + 1 < len(args):
            opts[args[i]] = args[i + 1]
            i += 2
        else:
            i += 1
    log_path = opts["--log"]
    state_dir = os.path.realpath(opts["--state-dir"]) if opts["--state-dir"] else None
    repo = opts["--repo"]

    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {"_unparsed": raw[:500]}

    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    cmd = tool_input.get("command") if isinstance(tool_input, dict) else None
    path = tool_input.get("file_path") if isinstance(tool_input, dict) else None

    denied, reason = decide(tool, cmd, path, state_dir, repo)

    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": tool,
        "cmd": cmd,
        "path": path,
        "denied": denied,
    }
    if denied:
        record["reason"] = reason
    if log_path:
        os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=True) + "\n")

    if denied:
        sys.stderr.write(f"watchdog guard: denied: {reason}\n")
        return 2
    return 0


# per subcommand: flag spelling -> canonical name; every allowlisted flag takes exactly one value
FLAGS = {
    "list": {"--repo": "repo", "-R": "repo", "--label": "label", "-l": "label", "--state": "state", "-s": "state",
             "--json": "json", "--limit": "limit", "-L": "limit"},
    "create": {"--repo": "repo", "-R": "repo", "--label": "label", "-l": "label", "--title": "title", "-t": "title",
               "--body-file": "body_file", "-F": "body_file"},
    "comment": {"--repo": "repo", "-R": "repo", "--body-file": "body_file", "-F": "body_file"},
}
POSITIONALS = {"list": 0, "create": 0, "comment": 1}


def decide(tool, cmd, path, state_dir, repo):
    """Return (denied: bool, reason: str)."""
    if tool == "Read":
        if not path or not state_dir:
            return True, "Read without a file_path inside the state dir"
        real = os.path.realpath(path)
        if real == state_dir or real.startswith(state_dir + os.sep):
            return False, ""
        return True, "Read outside the state dir"

    if tool != "Bash":
        return True, f"tool {tool!r} is not in the reporter's lane (Read, gh issue list|create|comment)"

    if not isinstance(cmd, str) or not cmd.strip():
        return True, "empty Bash command"
    if re.search(r"[$`;|&<>\n]", cmd):
        return True, "shell metacharacter ($ ` ; | & > < newline) in command"
    try:
        toks = shlex.split(cmd)
    except ValueError as exc:
        return True, f"unparseable command: {exc}"
    if len(toks) < 3 or toks[0] != "gh" or toks[1] != "issue" or toks[2] not in FLAGS:
        return True, "command is not gh issue list|create|comment"
    sub = toks[2]
    flags = FLAGS[sub]

    repo_seen = False
    positionals = []
    k = 3
    while k < len(toks):
        t = toks[k]
        if not t.startswith("-"):
            positionals.append(t)
            k += 1
            continue
        # a flag token: split `--long=value`; shorthand never takes an attached value
        if t.startswith("--") and "=" in t:
            name, val = t.split("=", 1)
            consumed = 1
        else:
            name = t
            if name not in flags:
                return True, f"flag {t!r} is not allowed for gh issue {sub}"
            if k + 1 >= len(toks):
                return True, f"flag {t!r} needs a value"
            val = toks[k + 1]
            consumed = 2
        if name not in flags:
            return True, f"flag {name!r} is not allowed for gh issue {sub}"
        if val == "" or val.startswith("-"):
            return True, f"value for {name!r} must not be empty or start with -"
        canon = flags[name]
        if canon == "repo":
            if val != repo:
                return True, f"--repo must be {repo}"
            repo_seen = True
        elif canon == "body_file":
            real = os.path.realpath(val)
            if not state_dir or not (real == state_dir or real.startswith(state_dir + os.sep)):
                return True, "--body-file must point inside the state dir"
        k += consumed
    if len(positionals) != POSITIONALS[sub]:
        return True, f"gh issue {sub} takes {POSITIONALS[sub]} positional argument(s), got {len(positionals)}"
    if sub == "comment" and not re.fullmatch(r"[0-9]{1,9}", positionals[0]):
        return True, "gh issue comment takes an issue number"
    if not repo_seen:
        return True, f"--repo {repo} is required"
    return False, ""


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # a broken guard must fail closed
        sys.stderr.write(f"watchdog guard: internal error, denying: {exc}\n")
        sys.exit(2)
