"""Sync operations: git pull + ansible apply, and push with security scan."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from rich.console import Console

from dotm.config import get_dotfiles_repo, get_excluded_modules
from dotm.modules import get_deploy_modules
from dotm.security import scan_changed_files, print_scan_results

console = Console()

# Fetch over HTTPS with a GIT_ASKPASS helper instead of the SSH origin: the
# 1Password SSH agent authorizes per top-level client process, so every
# launchd tick (a fresh `dotm sync`) either pops a Touch ID prompt or hangs
# ~60s and fails. This never touches the `origin` remote, which stays on SSH
# for interactive use.
HTTPS_FETCH_URL = "https://github.com/getfatday/dotfiles.git"
ASKPASS_HELPER = Path.home() / ".local" / "bin" / "dotm-git-askpass"


def _promptless_git_env() -> dict:
    """Env for a git invocation that must never block on a credential prompt."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = str(ASKPASS_HELPER)
    return env


def git_pull(repo_path, quiet: bool = False) -> tuple[bool, bool]:
    """Fetch over HTTPS (promptless) and rebase onto the fetched branch.

    Returns (success, updated) — `updated` is False when the repo was
    already up to date, so callers can skip the ansible apply.
    """
    if not quiet:
        console.print("[dim]Pulling latest changes...[/dim]")

    before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, cwd=repo_path,
    ).stdout.strip()
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, cwd=repo_path,
    ).stdout.strip()

    # Explicit refspec keeps origin/<branch> updated (like a normal `fetch
    # origin`) even though we're fetching from the HTTPS URL directly.
    fetch = subprocess.run(
        ["git", "-c", "credential.helper=", "fetch", "--quiet",
         HTTPS_FETCH_URL, f"+refs/heads/{branch}:refs/remotes/origin/{branch}"],
        capture_output=True, text=True, cwd=repo_path, timeout=60,
        env=_promptless_git_env(),
    )
    if fetch.returncode != 0:
        if not quiet:
            console.print(f"[red]Git fetch failed:[/red] {fetch.stderr.strip()}")
        return False, False

    rebase = subprocess.run(
        ["git", "rebase", f"origin/{branch}"],
        capture_output=True, text=True, cwd=repo_path, timeout=60,
    )
    if rebase.returncode != 0:
        if not quiet:
            console.print(f"[red]Git rebase failed:[/red] {rebase.stderr.strip()}")
        return False, False

    after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, cwd=repo_path,
    ).stdout.strip()

    updated = before != after
    if not quiet and updated and rebase.stdout.strip():
        console.print(f"  {rebase.stdout.strip()}")
    return True, updated


def ansible_apply(repo_path, excluded: list[str], quiet: bool = False) -> bool:
    """Run ansible-playbook with the effective module list."""
    deploy_yml = repo_path / "playbooks" / "deploy.yml"
    if not deploy_yml.exists():
        if not quiet:
            console.print("[red]deploy.yml not found[/red]")
        return False

    all_modules = get_deploy_modules()
    effective = [m for m in all_modules if m not in excluded]

    if not quiet:
        console.print(f"[dim]Applying {len(effective)} modules (excluding {len(excluded)})...[/dim]")

    # Build the install list as extra vars
    install_json = "[" + ", ".join(f'"{m}"' for m in effective) + "]"
    extra_vars = f'{{"final_modules": {install_json}}}'

    inventory = repo_path / "playbooks" / "inventory"
    cmd = [
        "ansible-playbook", str(deploy_yml),
        "-i", str(inventory),
        "--extra-vars", extra_vars,
    ]

    if quiet:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_path, timeout=600)
    else:
        result = subprocess.run(cmd, text=True, cwd=repo_path, timeout=600)

    if result.returncode != 0:
        if not quiet:
            console.print("[red]Ansible apply failed[/red]")
            if hasattr(result, "stderr") and result.stderr:
                console.print(result.stderr[:500])
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

    pull_ok, updated = git_pull(repo_path, quiet=quiet)
    if not pull_ok:
        return False

    if not updated:
        if not quiet:
            console.print("[dim]Already up to date — skipping apply.[/dim]")
        return True

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
