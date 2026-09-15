"""Sync operations: git pull + ansible apply, and push with security scan."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys

from rich.console import Console

from dotm.config import get_dotfiles_repo, get_excluded_modules
from dotm.security import scan_changed_files, print_scan_results

console = Console()


def _text(data) -> str:
    """Bytes or text from a subprocess, as text; None becomes the empty string."""
    if data is None:
        return ""
    if isinstance(data, (bytes, bytearray)):
        return data.decode("utf-8", "replace")
    return str(data)


def git_pull(repo_path, quiet: bool = False) -> bool:
    """Pull latest changes from remote."""
    if not quiet:
        console.print("[dim]Pulling latest changes...[/dim]")
    result = subprocess.run(
        ["git", "pull", "--rebase"],
        capture_output=True, text=True, cwd=repo_path, timeout=60,
    )
    if result.returncode != 0:
        if not quiet:
            console.print(f"[red]Git pull failed:[/red] {result.stderr.strip()}")
        return False
    if not quiet and result.stdout.strip() != "Already up to date.":
        console.print(f"  {result.stdout.strip()}")
    return True


def ansible_apply(repo_path, excluded: list[str], quiet: bool = False) -> bool:
    """Run ansible-playbook; deploy.yml resolves the module list for this host."""
    deploy_yml = repo_path / "playbooks" / "deploy.yml"
    if not deploy_yml.exists():
        if not quiet:
            console.print("[red]deploy.yml not found[/red]")
        return False

    if not quiet:
        console.print(
            f"[dim]Applying the module list deploy.yml resolves for this host "
            f"(excluding {len(excluded)})...[/dim]"
        )

    # deploy.yml is the single place a profile turns into a module list: it resolves the
    # list from profiles.yml (base_modules plus the host's profile). dotm hands it no list,
    # because an explicit list on the command line overrides that resolution and makes
    # profiles dead on the path machines actually use. The only extra var is this machine's
    # excluded_modules from the dotm config, which the play subtracts last.
    extra_vars = json.dumps({"dotm_excluded_modules": list(excluded)})

    inventory = repo_path / "playbooks" / "inventory"
    cmd = [
        "ansible-playbook", str(deploy_yml),
        "-i", str(inventory),
        "--extra-vars", extra_vars,
    ]

    # 1800 s: a first apply after new casks or npm installs can take well over 10 minutes.
    # The play runs in its own process group so a timeout kills Ansible's forked workers as
    # well (they otherwise outlive the run as orphans), and whatever Ansible printed before
    # the stop is written to the log. The timeout exception carries bytes, not text.
    timeout_s = 1800
    proc = subprocess.Popen(
        cmd, cwd=repo_path, start_new_session=True,
        stdout=subprocess.PIPE if quiet else None,
        stderr=subprocess.PIPE if quiet else None,
    )
    try:
        out_b, err_b = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out_b, err_b = proc.communicate()
        tail = (_text(out_b) or _text(exc.stdout))[-2000:]
        print(f"dotm sync: ansible-playbook exceeded {timeout_s} s and was stopped (process group killed).", file=sys.stderr)
        if tail:
            print("dotm sync: last Ansible output before the stop:\n" + tail, file=sys.stderr)
        return False

    if proc.returncode != 0:
        # Always leave the failure reason in the log, quiet or not: quiet runs feed launchd.
        err_tail = _text(err_b)[-2000:] if quiet else ""
        out_tail = _text(out_b)[-2000:] if quiet else ""
        print(f"dotm sync: ansible-playbook exited {proc.returncode}.", file=sys.stderr)
        if out_tail:
            print("dotm sync: last Ansible output:\n" + out_tail, file=sys.stderr)
        if err_tail:
            print("dotm sync: Ansible stderr:\n" + err_tail, file=sys.stderr)
        if not quiet:
            console.print("[red]Ansible apply failed[/red]")
        return False

    return True


def run_sync(quiet: bool = False) -> bool:
    """Full sync: pull + apply."""
    repo_path = get_dotfiles_repo()
    excluded = get_excluded_modules()

    if not repo_path.exists():
        if not quiet:
            console.print(f"[red]Dotfiles repo not found at {repo_path}[/red]")
        return False

    pull_ok = git_pull(repo_path, quiet=quiet)
    if not pull_ok:
        return False

    apply_ok = ansible_apply(repo_path, excluded, quiet=quiet)
    if not quiet:
        if apply_ok:
            console.print("[green]Sync complete.[/green]")
        else:
            console.print("[red]Sync failed during apply.[/red]")

    return apply_ok


def run_push(message: str | None = None, dry_run: bool = False) -> bool:
    """Security scan, commit, and push changes."""
    repo_path = get_dotfiles_repo()

    # Security scan first
    console.print("[dim]Scanning for secrets...[/dim]")
    findings = scan_changed_files(repo_path)
    if print_scan_results(findings, base_path=repo_path):
        console.print("[red]Push aborted — secrets detected. Remove them before pushing.[/red]")
        return False

    if dry_run:
        console.print("[dim]Dry run — would commit and push.[/dim]")
        return True

    # Check for changes
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=repo_path,
    )
    if not status.stdout.strip():
        console.print("[dim]Nothing to commit.[/dim]")
        return True

    # Stage module files and repo infrastructure
    subprocess.run(
        ["git", "add", "modules/", "playbooks/", "CLAUDE.md"],
        capture_output=True, text=True, cwd=repo_path,
    )

    # Commit
    if not message:
        message = "dotm: update modules"
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True, text=True, cwd=repo_path,
    )
    if result.returncode != 0:
        console.print(f"[red]Commit failed:[/red] {result.stderr.strip()}")
        return False
    console.print(f"  Committed: {message}")

    # Push
    result = subprocess.run(
        ["git", "push"],
        capture_output=True, text=True, cwd=repo_path, timeout=30,
    )
    if result.returncode != 0:
        console.print(f"[red]Push failed:[/red] {result.stderr.strip()}")
        return False

    console.print("[green]Pushed successfully.[/green]")
    return True
